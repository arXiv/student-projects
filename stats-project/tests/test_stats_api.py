import pytest
from browse.factory import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# You'll want to have the URI connected to a functioning database for this. 

# Test that the API returns JSON as expected for a valid query
def test_json_response(client):
    response = client.get('/api/get_data?model=hourly&group_by=start_dttm')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0  # Ensure it returns *some* data


# Test API response for bad parameters
def test_bad_params(client):
    # Invalid model name
    response = client.get('/api/get_data?model=foobar&group_by=start_dttm')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid model name \'foobar\'.'

    # Invalid group_by column
    response = client.get('/api/get_data?model=hourly&group_by=invalid_column')
    assert response.status_code == 400
    assert response.get_json()['error'] == "Invalid group_by column 'invalid_column' for model 'hourly'."

    # Missing required params
    response = client.get('/api/get_data')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Missing required parameters'


# Test aggregation by different time groups
@pytest.mark.parametrize('time_group', ['hour', 'day', 'month', 'year'])
def test_time_group_aggregation(client, time_group):
    response = client.get(f'/api/get_data?model=hourly&group_by=start_dttm&time_group={time_group}')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0  # Ensure that it returns data for the specified time group

    for item in data:
        assert time_group in item  # Ensure the time group exists in the response
        assert 'data' in item  # Ensure the aggregated data is present