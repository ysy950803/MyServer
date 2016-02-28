from mongoengine import Document, EmbeddedDocument, StringField, ListField, ReferenceField, EmbeddedDocumentField, \
    DateTimeField, \
    BooleanField, IntField, EmbeddedDocumentListField, ObjectIdField, DictField, NULLIFY, PULL, context_managers, DoesNotExist

from bson import ObjectId, DBRef
import datetime


def no_dereference_id_only(list_field):
    if list_field is None:
        return []
    with context_managers.no_dereference(list_field._instance.__class__):
        return map(lambda x: x.id, list_field)


def pull_from_reference_list(list_field, pk):
    document = list_field._instance
    document.update(**{'pull__' + list_field._name: DBRef(collection=document._cls, id=pk)})


def time_to_string(time_o):
    return time_o.strftime("%Y-%m-%d %H:%M:%S")
