using System.Globalization;
using System.Text.Json;
using Microsoft.AnalysisServices.Tabular;
using Microsoft.AnalysisServices.AdomdClient;

// Desktop owns the engine. desktop_smoke.ps1 scopes its process, port and cleanup.
var root = Path.GetFullPath(args[0]);
var port = int.Parse(args[1], CultureInfo.InvariantCulture);
var output = Path.GetFullPath(args[2]);
Directory.CreateDirectory(output);
var results = new List<object>();
var checks = 0;
using var server = new Server();
server.Connect("localhost:" + port);
var modelPath = Path.Combine(root, "DistroFit.SemanticModel", "model.bim");
var committed = Microsoft.AnalysisServices.Tabular.JsonSerializer.DeserializeDatabase(File.ReadAllText(modelPath));
server.Refresh();
if (server.Databases.Count != 1) throw new Exception("Expected the single owned Desktop model");
var db = server.Databases[0];
// Verify Desktop really opened the committed project, including expressions.
foreach (var table in committed.Model.Tables)
{
    var loaded = db.Model.Tables.Find(table.Name) ?? throw new Exception("Missing table: " + table.Name);
    foreach (var partition in table.Partitions)
    {
        var actual = loaded.Partitions[partition.Name].Source as CalculatedPartitionSource;
        var expectedSource = (CalculatedPartitionSource)partition.Source;
        if (actual?.Expression.Trim() != expectedSource.Expression.Trim())
            throw new Exception("Desktop partition differs: " + table.Name);
    }
    foreach (var measure in table.Measures)
        if (loaded.Measures[measure.Name].Expression.Trim() != measure.Expression.Trim())
            throw new Exception("Desktop measure differs: " + measure.Name);
}
if (db.Model.Relationships.Count != 3) throw new Exception("Desktop relationships differ");
db.Model.RequestRefresh(RefreshType.Full);
db.Model.SaveChanges();
using var connection = new AdomdConnection($"Data Source=localhost:{port};Initial Catalog={db.Name}");
connection.Open();
    var cases = System.Text.Json.JsonSerializer.Deserialize<JsonElement>(File.ReadAllText(Path.Combine(root, "checks.json")));
    foreach (var test in cases.EnumerateArray())
    {
        var query = test.GetProperty("query").GetString()!;
        using var command = new AdomdCommand(query, connection);
        using var reader = command.ExecuteReader();
        var rows = new List<Dictionary<string, object?>>();
        while (reader.Read())
        {
            var row = new Dictionary<string, object?>();
            for (var i = 0; i < reader.FieldCount; i++)
                row[reader.GetName(i)] = reader.IsDBNull(i) ? null : reader.GetValue(i);
            rows.Add(row);
        }
        var expected = test.GetProperty("expected");
        if (rows.Count != expected.GetArrayLength()) throw new Exception($"{test.GetProperty("name")}: row count {rows.Count} != {expected.GetArrayLength()}");
        var index = 0;
        foreach (var expectedRow in expected.EnumerateArray())
        {
            var row = rows[index++];
            foreach (var property in expectedRow.EnumerateObject())
            {
                var actual = row[property.Name];
                var value = property.Value;
                var equal = value.ValueKind switch
                {
                    JsonValueKind.Null => actual == null,
                    JsonValueKind.Number => actual != null && Math.Abs(Convert.ToDouble(actual, CultureInfo.InvariantCulture) - value.GetDouble()) <= 1e-8 * Math.Max(1, Math.Abs(value.GetDouble())),
                    _ => Convert.ToString(actual, CultureInfo.InvariantCulture) == value.GetString()
                };
                if (!equal) throw new Exception($"{test.GetProperty("name")} row {index} {property.Name}: {actual ?? "BLANK"} != {value}");
                checks++;
            }
        }
        results.Add(new { name = test.GetProperty("name").GetString(), query, rows });
    }
    Console.WriteLine($"PASS: {checks} native value checks in {results.Count} queries; engine {server.Version}");
    File.WriteAllText(Path.Combine(output, "native-results.json"), System.Text.Json.JsonSerializer.Serialize(new {
        status = "PASS", engine = "Microsoft Power BI Desktop Analysis Services", version = server.Version,
        modelSha256 = Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(modelPath))).ToLowerInvariant(),
        checks, queries = results.Count, results
    }, new JsonSerializerOptions { WriteIndented = true }));
