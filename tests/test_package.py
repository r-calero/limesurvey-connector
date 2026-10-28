import limesurvey_connector


def test_survey_structure_version():
    assert limesurvey_connector.SURVEY_STRUCTURE_VERSION == "2.1.0"
    assert limesurvey_connector.REFERENCE_IMPLEMENTATIONS == {
        "survey-structure": "2.1.0",
        "survey-data-dictionary": "2.1.0",
    }


def test_version_is_available():
    assert limesurvey_connector.__version__
