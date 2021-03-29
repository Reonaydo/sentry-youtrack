from hashlib import md5

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _
from requests.exceptions import ConnectionError, HTTPError, SSLError

from .youtrack import YouTrackClient


VERIFY_SSL_CERTIFICATE = getattr(
    settings, 'YOUTRACK_VERIFY_SSL_CERTIFICATE', True)


class YouTrackProjectForm(forms.Form):

    PROJECT_FIELD_PREFIX = 'field_'

    FIELD_TYPE_MAPPING = {
        'float': forms.FloatField,
        'integer': forms.IntegerField,
        'date': forms.DateField,
        'string': forms.CharField,
    }

    project_field_names = {}

    def __init__(self, project_fields=None, *args, **kwargs):
        super(YouTrackProjectForm, self).__init__(*args, **kwargs)
        if project_fields is not None:
            self.add_project_fields(project_fields)

    def add_project_fields(self, project_fields):
        fields = []
        for field in project_fields:
            form_field = self._get_form_field(field)
            if form_field:
                form_field.widget.attrs = {
                    'class': 'project-field',
                    'data-field': field['name']}
                index = len(fields) + 1
                field_name = '%s%s' % (self.PROJECT_FIELD_PREFIX, index)
                self.fields[field_name] = form_field
                fields.append(form_field)
                self.project_field_names[field_name] = field['name']
        return fields

    def get_project_field_values(self):
        self.full_clean()
        values = {}
        for form_field_name, name in self.project_field_names.items():
            values[name] = self.cleaned_data.get(form_field_name)
        return values

    def _get_initial(self, field_name):
        default_fields = self.initial.get('default_fields') or {}
        field_key = md5(force_bytes(field_name, errors='replace')).hexdigest()
        return default_fields.get(field_key)

    def _get_form_field(self, project_field):
        field_type = project_field['type']
        field_values = project_field['values']
        form_field = self.FIELD_TYPE_MAPPING.get(field_type)
        kwargs = {
            'label': project_field['name'],
            'required': False,
            'initial': self._get_initial(project_field['name'])}
        if form_field:
            return form_field(**kwargs)
        if field_values:
            choices = list(zip(field_values, field_values))
            if "[*]" in field_type:
                if kwargs['initial']:
                    kwargs['initial'] = kwargs['initial'].split(',')
                return forms.MultipleChoiceField(choices=choices, **kwargs)
            kwargs['choices'] = [('', '-----')] + choices
            return forms.ChoiceField(**kwargs)


class NewIssueForm(YouTrackProjectForm):

    title = forms.CharField(
        label=_("Title"),
        widget=forms.TextInput(attrs={'class': 'span9'}))
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={"class": 'span9'}))
    tags = forms.CharField(
        label=_("Tags"),
        help_text=_("Comma-separated list of tags"),
        widget=forms.TextInput(attrs={
            'class': 'span6', 'placeholder': "e.g. sentry"}),
        required=False)

    def clean_description(self):
        description = self.cleaned_data.get('description')
        # description = description.replace('```', '{quote}')
        return description


class AssignIssueForm(forms.Form):

    issue = forms.CharField(
        label=_("YouTrack Issue"),
        widget=forms.TextInput(
            attrs={'class': 'span6', 'placeholder': _("Choose issue")}))


class DefaultFieldForm(forms.Form):

    field = forms.CharField(required=True, max_length=255)
    value = forms.CharField(required=False, max_length=255)

    def __init__(self, plugin, project, *args, **kwargs):
        super(DefaultFieldForm, self).__init__(*args, **kwargs)
        self.plugin = plugin
        self.project = project

    def save(self):
        data = self.cleaned_data
        default_fields = self.plugin.get_option(
            self.plugin.default_fields_key, self.project) or {}
        default_fields[md5(force_bytes(data['field'], errors='replace')).hexdigest()] = data['value']
        self.plugin.set_option(
            self.plugin.default_fields_key, default_fields, self.project)
