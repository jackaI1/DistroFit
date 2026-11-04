using System.Diagnostics;
using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;
using Microsoft.AnalysisServices.Tabular;
using Microsoft.AnalysisServices.AdomdClient;

// The only server started here is owned by this process and bound to loopback.
// No installed user instance is discovered, modified or stopped.
var root = Path.GetFullPath(args[0]);
var engine = Path.GetFullPath(args[1]);
var output = Path.GetFullPath(args[2]);
Directory.CreateDirectory(output);
var work = Path.Combine(Path.GetTempPath(), "DistroFit-native-" + Guid.NewGuid());
Directory.CreateDirectory(work);
var config = new XElement("ConfigurationSettings",
    new XElement("DataDir", work), new XElement("TempDir", work),
    new XElement("LogDir", work), new XElement("BackupDir", work),
    new XElement("DeploymentMode", 1), new XElement("RecoveryModel", 1),
    new XElement("DisklessModeRequested", 1), new XElement("Port", 0),
    new XElement("PrivateProcess", Environment.ProcessId), new XElement("InstanceVisible", 0),
    new XElement("Language", 0),
    new XElement("Network", new XElement("ListenOnlyOnLocalConnections", 1)),
    new XElement("Log", new XElement("FlightRecorder", new XElement("Enabled", 0))));
config.Save(Path.Combine(work, "msmdsrv.ini"));
Process? process = null;
var results = new List<object>();
var checks = 0;
var success = false;
var port = "";
string? started = null;
try
{
    process = Process.Start(new ProcessStartInfo(engine, $"-c -n {Guid.NewGuid()} -s \"{work}\"")
        { WorkingDirectory = work, UseShellExecute = false, CreateNoWindow = true })!;
    started = process.StartTime.ToUniversalTime().ToString("O");
    Console.WriteLine($"Owned engine PID={process.Id}, started={started}; cleanup via XMLA Shutdown then exact PID fallback");
    var portFile = Path.Combine(work, "msmdsrv.port.txt");
    var deadline = DateTime.UtcNow.AddSeconds(60);
    while (!File.Exists(portFile) && !process.HasExited && DateTime.UtcNow < deadline)
        Thread.Sleep(250);
    if (!File.Exists(portFile)) throw new Exception("Engine did not start: " + string.Join("\n", Directory.GetFiles(work, "*.log").SelectMany(p => File.ReadLines(p).TakeLast(15))));
    port = File.ReadAllText(portFile, Encoding.Unicode).Trim();
    Console.WriteLine("Owned loopback port=" + port);
    using var server = new Server();
    server.Connect("localhost:" + port);
    var modelPath = Path.Combine(root, "DistroFit.SemanticModel", "model.bim");
    var db = Microsoft.AnalysisServices.Tabular.JsonSerializer.DeserializeDatabase(File.ReadAllText(modelPath));
    server.Databases.Add(db);
    db.Update(Microsoft.AnalysisServices.UpdateOptions.ExpandFull);
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
    success = true;
    Console.WriteLine($"PASS: {checks} native value checks in {results.Count} queries; engine {server.Version}");
    File.WriteAllText(Path.Combine(output, "native-results.json"), System.Text.Json.JsonSerializer.Serialize(new {
        status = "PASS", engine = "Microsoft Power BI Desktop Analysis Services", version = server.Version,
        modelSha256 = Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(modelPath))).ToLowerInvariant(),
        checks, queries = results.Count, results
    }, new JsonSerializerOptions { WriteIndented = true }));
}
finally
{
    if (process != null && !process.HasExited)
    {
        try
        {
            using var shutdown = new Server();
            shutdown.Connect("localhost:" + port);
            shutdown.Execute("<Shutdown xmlns=\"http://schemas.microsoft.com/analysisservices/2003/engine\" />");
        }
        catch { /* Some Desktop engine versions close before acknowledging Shutdown. */ }
        if (!process.WaitForExit(10000)) { process.Kill(); process.WaitForExit(10000); }
    }
    var stopped = process == null || process.HasExited;
    File.WriteAllText(Path.Combine(output, "cleanup.json"), System.Text.Json.JsonSerializer.Serialize(new {
        pid = process?.Id, started, port, stopped, success,
        owner = "DistroFit NativeCheck", cleanup = "XMLA Shutdown; exact owned PID fallback",
        workingDirectoryRemoved = true
    }, new JsonSerializerOptions { WriteIndented = true }));
    process?.Dispose();
    Directory.Delete(work, true);
    if (!stopped) throw new Exception("Owned engine failed to stop");
    Console.WriteLine("Cleanup: owned engine stopped and temporary data removed");
}
