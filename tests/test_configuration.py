from sentry_youtrack.configuration import YouTrackConfiguration
from unittest import  TestCase
from vcr import VCR
import os

PROJECT_ID = 'myproject'

vcr = VCR(path_transformer=VCR.ensure_suffix('.yaml'),
          cassette_library_dir=os.path.join('tests', 'cassettes'))
print(os.path.join('tests', 'cassettes'))

class TestYouTrackConfiguration(TestCase):
    def setUp(self):
        self.url = 'https://youtrack.myjetbrains.com'
        self.username = 'root'
        self.password = 'admin'
        self.invalid_url = 'https://example.youtrack.example'
    
    def assert_fields_equal(self, field_names, config):
        assert sorted([field['name'] for field in config]) == sorted(field_names)

    def test_renders_no_input(self):
        yt_config = YouTrackConfiguration({})
        self.assert_fields_equal(['password', 'url', 'username'], yt_config.config)
        assert not yt_config.client_errors
    
    def test_renders_with_partial_input(self):
        yt_config = YouTrackConfiguration({'url': self.invalid_url, 'username': 'bob101'})
        self.assert_fields_equal(['password', 'url', 'username'], yt_config.config)
        assert not yt_config.client_errors

    def test_renders_with_full_invalid_input(self):
        yt_config = YouTrackConfiguration({'url': self.invalid_url, 'username': 'bob101', 'password':'12345'})
        self.assert_fields_equal(['password', 'url', 'username'], yt_config.config)
        assert len(yt_config.client_errors) == 1

    @vcr.use_cassette('yt_config.yaml')
    def test_renders_with_full_valid_input(self):
        yt_config = YouTrackConfiguration({'url': self.url, 'username': self.username, 'password':self.password})
        fields = ['default_tags', 'ignore_fields', 'password', 'project', 'url', 'username']
        self.assert_fields_equal(fields, yt_config.config)
        assert not yt_config.client_errors
