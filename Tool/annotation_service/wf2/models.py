from django.db import models
from accounts.models import User
from wf1.models import Claim
from wiki.models import Sentence, Hyperlink

LABELS = [(0, 'Supported'), (1, 'Refuted')]
CLAIM_STATES = [(0, 'Assigned'), (1, 'Not enough information'), (2, 'Don\'t want to annotate'),
                (3, 'Check WF1 rules'), (4, 'Simple error'), (5, 'Flag'), (6, 'Completed')]


class Evidence(models.Model):
    hyperlinks = models.ManyToManyField(Hyperlink, related_name='evidences')
    sentences = models.ManyToManyField(Sentence, related_name='evidences')
    last_update = models.DateTimeField(auto_now=True)


class Label(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='labels', null=False)
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE, related_name='labels', null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='labels', null=False)
    label = models.IntegerField(choices=LABELS)
    evidence = models.OneToOneField(Evidence, on_delete=models.CASCADE, related_name='label', null=True)
    last_update = models.DateTimeField(auto_now=True)


class ClaimState(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claim_state', null=False)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='claim_state', null=False)
    state = models.IntegerField(choices=CLAIM_STATES)
    last_update = models.DateTimeField(auto_now=True)
