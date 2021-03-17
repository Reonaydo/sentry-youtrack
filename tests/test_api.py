import os

import pytest
from vcr import VCR

from sentry_youtrack.youtrack import YouTrackClient


PROJECT_ID = 'myproject'

vcr = VCR(path_transformer=VCR.ensure_suffix('.yaml'),
          cassette_library_dir=os.path.join('tests', 'cassettes'))


@pytest.fixture
def youtrack_client():
    with vcr.use_cassette('youtrack_client.yaml'):
        client = YouTrackClient('https://youtrack.myjetbrains.com',
                                username='root', password='admin')
    return client


@vcr.use_cassette
def test_get_api_key(youtrack_client):
    assert youtrack_client.api_key == 'abcd1234'


@vcr.use_cassette
def test_get_project_name(youtrack_client):
    assert youtrack_client.get_project_name(PROJECT_ID) == 'My project'


@vcr.use_cassette
def test_get_projects(youtrack_client):
    expected_projects = [
        {'id': 'myproject', 'name': 'My project'},
        {'id': 'testproject', 'name': 'Test project'}]
    assert list(youtrack_client.get_projects()) == expected_projects


@vcr.use_cassette
def test_get_priorities(youtrack_client):
    priorities = ['Show-stopper', 'Critical', 'Major', 'Normal', 'Minor']
    assert youtrack_client.get_priorities() == priorities


@vcr.use_cassette
def test_get_issue_types(youtrack_client):
    types = ['Bug', 'Cosmetics', 'Exception', 'Feature', 'Task', 
             'Usability Problem', 'Performance Problem', 'Epic', 
             'Meta Issue', 'Auto-reported exception']
    assert youtrack_client.get_issue_types() == types


@vcr.use_cassette
def test_get_project_fields(youtrack_client):
    fields = [
        {'name': 'Priority',
         'values': ['Show-stopper', 'Critical', 'Major', 'Normal', 'Minor'],
         'empty_text': 'No Priority',
         'type': 'enum[1]'},
        {'name': 'Type',
         'values': ['Bug', 'Cosmetics', 'Exception', 'Feature', 'Task',
                    'Usability Problem', 'Performance Problem', 'Epic',
                    'Meta Issue', 'Auto-reported exception'], 
         'empty_text': 'No Type', 
         'type': 'enum[1]'}, 
        {'name': 'State',
         'values': ['Submitted', 'Open', 'In Progress', 'To be discussed', 
                    'Reopened', "Can't Reproduce", 'Duplicate', 'Fixed', 
                    "Won't fix", 'Incomplete', 'Obsolete',
                    'Verified', 'New'],
         'empty_text': 'No State', 
         'type': 'state[1]'}, 
        {'name': 'Assignee',
         'values': ['root'], 
         'empty_text': 'Unassigned', 
         'type': 'user[1]'}, 
        {'name': 'Subsystem',
         'values': ['No subsystem'], 
         'empty_text': 'No Subsystem', 
         'type': 'ownedField[1]'}, 
        {'name': 'Fix versions',
         'values': [], 
         'empty_text': 'Unscheduled', 
         'type': 'version[*]'}, 
        {'name': 'Affected versions',
         'values': [], 
         'empty_text': 'Unknown', 
         'type': 'version[*]'}, 
        {'name': 'Fixed in build',
         'values': [], 
         'empty_text': 'Next Build', 
         'type': 'build[1]'}]
    assert list(youtrack_client.get_project_fields(PROJECT_ID)) == fields
