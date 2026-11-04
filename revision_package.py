"""Choose revision-consistent BOM metadata before releasing a review package."""


def select_bom_revision(drawing_revision, approved_bom_revision, cached_bom_revision=None):
    """Return the approved BOM revision only when it matches the drawing.

    A bill of materials (BOM) lists the parts in a drawing. Call this before
    copying the approved BOM into a package. Cache metadata is accepted to make
    the handoff explicit, but never authorizes release. Revisions are exact,
    case-sensitive identifiers; ambiguous whitespace is rejected, not guessed.
    This checks metadata, not the contents or authenticity of a drawing file.
    """
    for value in (drawing_revision, approved_bom_revision):
        if not isinstance(value, str) or not value or value.strip() != value:
            raise ValueError("Drawing and approved BOM need nonempty, unambiguous revision identifiers")
    if drawing_revision != approved_bom_revision:
        raise ValueError("Approved BOM revision does not match the drawing; block release")
    return approved_bom_revision
