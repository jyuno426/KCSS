# Generated by Django 3.0.8 on 2020-08-09 11:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kcss', '0014_auto_20200809_1828'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coauthorship',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coauthorship', to='kcss.Author'),
        ),
    ]
