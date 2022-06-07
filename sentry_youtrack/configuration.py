# -*- encoding: utf-8 -*-
from requests.exceptions import ConnectionError, HTTPError, SSLError
from sentry.exceptions import PluginError
from django.utils.translation import ugettext_lazy as _
from sentry_youtrack.forms import VERIFY_SSL_CERTIFICATE
from sentry_youtrack.youtrack import YouTrackClient


class YouTrackConfiguration(object):

    error_message = {
        'client': _("Unable to connect to YouTrack."),
        'project_unknown': _('Unable to fetch project'),
        'project_not_found': _('Project not found: %s'),
        'invalid_ssl': _("SSL certificate  verification failed."),
        'invalid_api_key': _('Invalid username or api_key.'),
        'invalid_project': _('Invalid project: \'%s\''),
        'missing_fields': _('Missing required fields.'),
        'perms': _("User doesn't have Low-level Administration permissions."),
        'required': _("This field is required.")}

    def __init__(self, initial):
        self.config = self.build_default_fields(initial)
        self.client_errors = {}
        if self.has_client_fields(initial):
            client = self.get_youtrack_client(initial)
            yt_project = initial.get('project')
            if client:
                choices = []
                if yt_project:
                    choices = self.get_ignore_field_choices(client, yt_project)
                self.config.append({
                    'name':'ignore_fields',
                    'label':'Ignore Fields',
                    'type':'select',
                    'choices':choices,
                    'required':False,
                    'help': 'These fields will not appear on the form.',
                })
                choices = self.get_project_field_choices(client, yt_project)
                self.config.append({
                    'name':'project',
                    'label':'Linked Project',
                    'type':'select',
                    'choices': choices,
                    'required':True,})

                self.__add_default_tags()

    def has_client_fields(self, initial):
        return initial.get('api_key') and initial.get('username') and initial.get('url')

    def build_default_fields(self, initial):
        url = {'name':'url',
                'label':'YouTrack Instance URL',
                'type':'text',
                'required':True,
                'placeholder': 'e.g. "https://yoursitename.myjetbrains.com/youtrack/"',}
        username = {'name':'username',
                'label':'Username',
                'type':'text',
                'required':True,
                'help': 'User should have admin rights.',}
        api_key = {'name':'api_key',
                'label':'API key',
                'type':'secret',
                'required':False,
                'help': 'Only enter a api_key if you want to change it.',}
        if initial.get('api_key'):
            api_key['has_saved_value'] = True

        return [url, username, api_key]

    def __add_default_tags(self):
        self.config.append({'name':'default_tags',
            'label':'Default Tags',
            'type':'text',
            'required':False,
            'placeholder': 'e.g. sentry',
            'help': 'Comma-separated list of tags.',})

    def get_youtrack_client(self, data, additional_params=None):
        yt_settings = {
            'url': data.get('url'),
            'username': data.get('username'),
            'api_key': data.get('api_key'),
            'verify_ssl_certificate': VERIFY_SSL_CERTIFICATE}
        if additional_params:
            yt_settings.update(additional_params)

        client = None
        try:
            client = YouTrackClient(**yt_settings)
        except (HTTPError, ConnectionError) as e:
            if e.response is not None and e.response.status_code == 403:
                self.client_errors['username'] = self.error_message[
                    'invalid_api_key']
            else:
                self.client_errors['url'] = self.error_message['client']
        except (SSLError, TypeError) as e:
            self.client_errors['url'] = self.error_message['invalid_ssl']
        if client:
            try:
                client.get_user(yt_settings.get('username'))
            except HTTPError as e:
                if e.response.status_code == 403:
                    self.client_errors['username'] = self.error_message['perms']
                    client = None
        return client

    def get_ignore_field_choices(self, client, project):
        try:
            fields = list(client.get_project_fields_list(project))
        except HTTPError:
            self.client_errors['project'] = self.error_message[
                'invalid_project'] % (project,)
        else:
            names = [field['name'] for field in fields]
            return list(zip(names, names))
        return []

    def get_project_field_choices(self, client, project):
        choices = [(' ', "- Choose project -")]
        try:
            projects = list(client.get_projects())
        except HTTPError:
            self.client_errors['project'] = self.error_message[
                'invalid_project'] % (project, )
        else:
            for project in projects:
                display = "%s (%s)" % (project['name'], project['id'])
                choices.append((project['id'], display))
        return choices

    def get_project_fields_list(self, client, project_id):
        try:
            return list(client.get_project_fields_list(project_id))
        except (HTTPError, ConnectionError) as e:
            if e.response is not None and e.response.status_code == 404:
                self.client_errors['project'] = self.error_message['project_not_found'] % project_id
            else:
                self.client_errors['project'] = self.error_message['project_unknown']

    def get_projects(self, client, project_id):
        try:
            return list(client.get_projects())
        except (HTTPError, ConnectionError) as e:
            if e.response is not None and e.response.status_code == 404:
                self.client_errors['project'] = self.error_message['project_not_found'] % project_id
            else:
                self.client_errors['project'] = self.error_message['project_unknown']
