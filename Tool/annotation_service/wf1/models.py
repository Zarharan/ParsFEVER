from django.db import models
from accounts.models import User
from wiki.models import *

MUTATION_TYPES = [(0, 'Rephrase'), (1, 'Negate'), (2, 'Similar'),
                  (3, 'Dissimilar'), (4, 'More specific'), (5, 'More general')]


class Claim(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    claim_content = models.TextField()
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='claims', null=False)
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE, related_name='claims', null=False)
    parent_claim = models.ForeignKey("Claim", on_delete=models.CASCADE, related_name='children', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claims', null=False)
    mutation_type = models.IntegerField(choices=MUTATION_TYPES, blank=True, null=True)
    by_supervisor = models.BooleanField(default=False)
    checked_by_supervisor = models.BooleanField(default=False)
    annotated_count = models.IntegerField(default=0)
    last_update = models.DateTimeField(auto_now=True)
