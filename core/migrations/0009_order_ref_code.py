# Generated by Django 2.2.8 on 2020-09-28 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20200928_1631'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='ref_code',
            field=models.CharField(default='ACef134', max_length=20),
            preserve_default=False,
        ),
    ]
