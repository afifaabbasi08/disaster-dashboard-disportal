from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('disaster_data', '0006_uploadeddataset'),
    ]

    operations = [
        migrations.CreateModel(
            name='Landslide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('place', models.CharField(max_length=255)),
                ('trigger', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
            ],
        ),
    ]
