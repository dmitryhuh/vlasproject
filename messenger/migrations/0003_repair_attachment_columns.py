from django.db import migrations

def repair_missing_columns(apps, schema_editor):
    Message = apps.get_model("messenger", "Message")
    connection = schema_editor.connection
    table_name = Message._meta.db_table

    with connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }

    for field_name in ("file", "original_filename", "file_size"):
        if field_name not in existing_columns:
            schema_editor.add_field(Message, Message._meta.get_field(field_name))

class Migration(migrations.Migration):
    dependencies = [
        ("messenger", "0002_message_attachments"),
    ]

    operations = [
        migrations.RunPython(repair_missing_columns, migrations.RunPython.noop),
    ]
