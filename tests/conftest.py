"""
Pytest fixtures
"""
import pytest


@pytest.fixture(name='fake_data')
def fixture_fake_data() -> dict:
    """
    Fixture to create a fake data dict for testing

    :return:
    """
    return {
        'media': [
            {
                'title': 'title-1',
                'filename': 'filename-1',
            },
            {
                'title': 'title-2',
                'filename': 'filename-2',
            },
            {
                'title': 'title-3',
                'filename': 'filename-3',
            },
            {
                'title': 'title-4',
                'filename': 'filename-4',
            },
            {
                'title': 'title-5',
                'filename': 'filename-5',
            }
        ]
    }
