from django.db import models
from accounts.models import User

PAGE_STATUS = [(0, 'Not used'), (1, 'Chosen'), (2, 'Claim generated'), (3, 'Completed')]


class Page(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    token = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    page_content = models.TextField()
    page_content_html = models.TextField()
    status = models.IntegerField(choices=PAGE_STATUS, default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pages', null=True)
    useless = models.BooleanField(default=False)
    as_evidence = models.BooleanField(default=False)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Sentence(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    sentence_content = models.TextField()
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='sentences', null=False)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sentence_content


class Hyperlink(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    token = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    first_paragraph = models.TextField()
    pages = models.ManyToManyField(Page, related_name='hyperlinks')
    sentences = models.ManyToManyField(Sentence, related_name='hyperlinks')
    last_update = models.DateTimeField(auto_now=True)
