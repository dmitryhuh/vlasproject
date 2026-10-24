

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('made_app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='conversation',
            name='participants',
        ),
        migrations.RemoveField(
            model_name='message',
            name='conversation',
        ),
        migrations.AlterUniqueTogether(
            name='follow',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='follow',
            name='follower',
        ),
        migrations.RemoveField(
            model_name='follow',
            name='following',
        ),
        migrations.RemoveField(
            model_name='message',
            name='sender',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='post',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='sender',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='user',
        ),
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-created_at']},
        ),
        migrations.RemoveField(
            model_name='post',
            name='hashtags',
        ),
        migrations.RemoveField(
            model_name='post',
            name='image',
        ),
        migrations.RemoveField(
            model_name='post',
            name='link',
        ),
        migrations.RemoveField(
            model_name='post',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='bio',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='name',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='username',
        ),
        migrations.DeleteModel(
            name='Bookmark',
        ),
        migrations.DeleteModel(
            name='Conversation',
        ),
        migrations.DeleteModel(
            name='Follow',
        ),
        migrations.DeleteModel(
            name='Message',
        ),
        migrations.DeleteModel(
            name='Notification',
        ),
    ]
