Option Explicit

Public Sub ShowReviewForm()
    ReviewForm.Show
End Sub

Public Function RefreshReview(ByVal dataset As String, ByVal distribution As String) As Boolean
    Dim models As Worksheet, plots As Worksheet, target As Worksheet
    Dim r As Long, lastModel As Long, lastPlot As Long, count As Long, pointCount As Long
    Dim selected As Boolean, outRow As Long
    On Error GoTo InvalidSelection
    Set models = ThisWorkbook.Worksheets("ModelStore")
    Set plots = ThisWorkbook.Worksheets("PlotStore")
    Set target = ThisWorkbook.Worksheets("Comparison")
    lastModel = models.Cells(models.Rows.Count, 1).End(xlUp).Row
    lastPlot = plots.Cells(plots.Rows.Count, 1).End(xlUp).Row
    ' Validate everything before replacing the last good view.
    For r = 2 To lastModel
        If CStr(models.Cells(r, 1).Value2) = dataset Then
            count = count + 1
            If CStr(models.Cells(r, 2).Value2) = distribution Then selected = True
        End If
    Next r
    If Not selected Or count > 14 Then Err.Raise 5, , "Choose a saved dataset and curve from the lists."
    For r = 2 To lastPlot
        If CStr(plots.Cells(r, 1).Value2) = dataset And CStr(plots.Cells(r, 2).Value2) = distribution Then
            If Not IsNumeric(plots.Cells(r, 3).Value2) Then Err.Raise 5, , "The saved plot has an invalid value."
            If Not IsNumeric(plots.Cells(r, 4).Value2) Then Err.Raise 5, , "The saved plot has an invalid value."
            If Not IsNumeric(plots.Cells(r, 5).Value2) Then Err.Raise 5, , "The saved plot has an invalid value."
            pointCount = pointCount + 1
        End If
    Next r
    If pointCount <> 40 Then Err.Raise 5, , "The saved plot must contain 40 points. Rebuild the workbook."
    target.Range("A10:G23").ClearContents
    target.Range("I10:K49").ClearContents
    outRow = 10
    For r = 2 To lastModel
        If CStr(models.Cells(r, 1).Value2) = dataset Then
            target.Cells(outRow, 1).Resize(1, 7).Value2 = models.Cells(r, 2).Resize(1, 7).Value2
            outRow = outRow + 1
        End If
    Next r
    outRow = 10
    For r = 2 To lastPlot
        If CStr(plots.Cells(r, 1).Value2) = dataset And CStr(plots.Cells(r, 2).Value2) = distribution Then
            target.Cells(outRow, 9).Resize(1, 3).Value2 = plots.Cells(r, 3).Resize(1, 3).Value2
            outRow = outRow + 1
        End If
    Next r
    ' Text format prevents names beginning with = from becoming formulas.
    target.Range("B3:B4").NumberFormat = "@"
    target.Range("B3").Value2 = dataset
    target.Range("B4").Value2 = distribution
    target.Range("B6").Value2 = "Updated saved fits. Cleaned measurements need a new Python fit."
    target.Calculate
    RefreshReview = True
    Exit Function
InvalidSelection:
    ThisWorkbook.Worksheets("Comparison").Range("B6").Value2 = Err.Description
    RefreshReview = False
End Function
