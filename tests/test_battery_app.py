from pathlib import Path
from streamlit.testing.v1 import AppTest

PAGE = Path(__file__).resolve().parents[1] / "pages" / "5_Battery_fleet.py"


def test_battery_page_uses_measured_study_and_filters_cells():
    app = AppTest.from_file(str(PAGE), default_timeout=45).run()
    assert not app.exception
    assert app.metric[0].value == "504"
    assert app.metric[2].value == "1"
    app.multiselect[0].set_value(["B0006"]).run()
    assert not app.exception
    assert app.metric[0].value == "168"
    assert set(app.dataframe[0].value.cell) == {"B0006"}
    assert app.dataframe[1].value.flagged_cycle.all()
    app.checkbox[0].uncheck().run()
    assert len(app.dataframe[1].value) == 168
    app.multiselect[0].set_value([]).run()
    assert not app.exception and app.info
    assert not app.get("download_button")
