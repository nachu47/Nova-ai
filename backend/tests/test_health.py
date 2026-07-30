def test_live(client):
    response=client.get('/api/v1/health/live');assert response.status_code==200;assert response.json()=={'status':'alive'}
