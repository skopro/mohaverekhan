# Generated by Django 2.1.7 on 2019-03-28 16:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mohaverekhan', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NLTKTagger',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('mohaverekhan.tagger',),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together={('name', 'tag_set'), ('persian', 'tag_set')},
        ),
    ]