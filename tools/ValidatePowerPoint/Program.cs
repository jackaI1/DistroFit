using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Validation;

if (args.Length == 0) throw new ArgumentException("Pass at least one PPTX path");
int failures = 0;
foreach (string file in args) {
    using var deck = PresentationDocument.Open(file, false);
    var errors = new OpenXmlValidator().Validate(deck).ToList();
    foreach (var error in errors.Take(20))
        Console.Error.WriteLine($"{file}: {error.Part?.Uri} {error.Path?.XPath}: {error.Description}");
    // Validate the data workbook as well as its presentation container.
    foreach (var chart in deck.PresentationPart!.SlideParts.SelectMany(s => s.ChartParts)) {
        using var stream = chart.EmbeddedPackagePart!.GetStream();
        using var book = SpreadsheetDocument.Open(stream, false);
        var bookErrors = new OpenXmlValidator().Validate(book).ToList();
        foreach (var error in bookErrors.Take(10)) Console.Error.WriteLine(error.Description);
        errors.AddRange(bookErrors);
    }
    Console.WriteLine($"{file}: {errors.Count} Office schema errors");
    failures += errors.Count;
}
return failures == 0 ? 0 : 1;
