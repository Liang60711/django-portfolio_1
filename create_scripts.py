import os 
import django 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from core.models import Item
import random
from django.core.files import File
from django.conf import settings



CATEGORY_CHOICES = (
    ('S', 'Shirt'),
    ('SW', 'Sport wear'),
    ('OW', 'Outwear'),
)


LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger'),
)


ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)


Item.objects.all().delete()


f = File(open(os.path.join(settings.BASE_DIR, 'media', '5.jpg'), 'rb'))

for i in range(12):
    Item.objects.create(
        title='Item '+str(i),
        price=random.randint(1,9)*100,
        category=random.choices(CATEGORY_CHOICES)[0][0],
        label=random.choices(LABEL_CHOICES)[0][0],
        description='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec pretium ante erat, vitae sodales mi varius quis. Etiam vestibulum lorem vel urna tempor, eu fermentum odio aliquam. Aliquam consequat urna vitae ipsum pulvinar, in blandit purus eleifend.',
        slug=str(i),
        image=f,
    )