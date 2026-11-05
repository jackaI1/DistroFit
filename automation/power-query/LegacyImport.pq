let
    Source = Csv.Document(LegacyCsvBinary, [Delimiter=";", Encoding=65001]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Names = Table.TransformColumnNames(Headers, each Text.Lower(Text.Trim(_))),
    Required = Table.SelectColumns(Names, {"dataset", "value", "unit"}),
    Indexed = Table.AddIndexColumn(Required, "source_row", 2, 1, Int64.Type),
    Trimmed = Table.TransformColumns(Indexed, {
        {"dataset", each if _ = null then "" else Text.Trim(_), type text},
        {"value", each if _ = null then "" else Text.Trim(_), type text},
        {"unit", each if _ = null then "" else Text.Lower(Text.Trim(_)), type text}
    }),
    Parsed = Table.AddColumn(Trimmed, "numeric_value", each
        let Numeric = try Number.From(Text.Replace([value], ",", "."), "en-US") otherwise null
        in if Numeric = null then null
           else if Numeric > -#infinity and Numeric < #infinity then Numeric
           else null, type nullable number),
    Flagged = Table.AddColumn(Parsed, "import_flag", each
        if [dataset] = "" or [value] = "" or [unit] = "" then "BLANK"
        else if [numeric_value] = null then "INVALID_NUMBER" else "OK", type text),
    RemovedText = Table.RemoveColumns(Flagged, {"value"}),
    Renamed = Table.RenameColumns(RemovedText, {{"numeric_value", "value"}}),
    Result = Table.ReorderColumns(Renamed, {"dataset", "value", "unit", "source_row", "import_flag"})
in
    Result
