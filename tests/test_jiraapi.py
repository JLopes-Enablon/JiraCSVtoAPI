import pytest
from unittest.mock import patch, MagicMock
from jiraapi import JiraAPI

@patch('jiraapi.requests')
def test_get_issue(mock_requests):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {'fields': {'customfield_10016': 5}}
    mock_response.status_code = 200
    mock_requests.get.return_value = mock_response

    jira = JiraAPI(base_url='http://fake-url', email='test@example.com', api_token='fake-token')
    issue = jira.get_issue('FAKE-1')
    assert issue['fields']['customfield_10016'] == 5

# Add more tests for other methods in JiraAPI as needed
