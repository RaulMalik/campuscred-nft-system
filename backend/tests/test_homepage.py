"""
Tests for homepage and basic routes
"""
import pytest


class TestHomepage:
    """Test homepage functionality"""

    def test_homepage_loads(self, client):
        """Test homepage loads successfully"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'CampusCred' in response.data
        assert b'Welcome' in response.data

    def test_auth_test_endpoint(self, client):
        """Test auth test endpoint"""
        response = client.get('/auth/test')
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Auth blueprint is working!'