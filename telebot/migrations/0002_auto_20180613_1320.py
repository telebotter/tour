# Generated by Django 2.0.3 on 2018-06-13 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telebot', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='created',
            field=models.DateTimeField(auto_created=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='telegram_id',
            field=models.IntegerField(default=1, unique=True),
            preserve_default=False,
        ),
    ]
