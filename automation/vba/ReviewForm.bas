Option Explicit

Private Sub UserForm_Initialize()
    Dim index As Worksheet, r As Long, lastRow As Long
    DatasetBox.Style = 2
    DistributionBox.Style = 2
    Set index = ThisWorkbook.Worksheets("DatasetIndex")
    lastRow = index.Cells(index.Rows.Count, 1).End(xlUp).Row
    DatasetBox.Clear
    For r = 2 To lastRow
        DatasetBox.AddItem CStr(index.Cells(r, 1).Value2)
    Next r
    If DatasetBox.ListCount > 0 Then DatasetBox.ListIndex = 0
    StatusLabel.Caption = "Choose a saved sample and curve, then refresh."
End Sub

Private Sub DatasetBox_Change()
    Dim models As Worksheet, r As Long, lastRow As Long
    Set models = ThisWorkbook.Worksheets("ModelStore")
    lastRow = models.Cells(models.Rows.Count, 1).End(xlUp).Row
    DistributionBox.Clear
    For r = 2 To lastRow
        If CStr(models.Cells(r, 1).Value2) = CStr(DatasetBox.Value) Then
            DistributionBox.AddItem CStr(models.Cells(r, 2).Value2)
        End If
    Next r
    If DistributionBox.ListCount > 0 Then DistributionBox.ListIndex = 0
End Sub

Private Sub RefreshButton_Click()
    If DatasetBox.ListIndex < 0 Or DistributionBox.ListIndex < 0 Then
        StatusLabel.Caption = "Choose both a dataset and a curve."
        Exit Sub
    End If
    If RefreshReview(CStr(DatasetBox.Value), CStr(DistributionBox.Value)) Then
        StatusLabel.Caption = "Comparison and both charts updated."
    Else
        StatusLabel.Caption = CStr(ThisWorkbook.Worksheets("Comparison").Range("B6").Value2)
    End If
End Sub

Private Sub CloseButton_Click()
    Unload Me
End Sub
