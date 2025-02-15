from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save

# class User(AbstractUser):
#     username = models.CharField(unique=True, max_length=100)
#     email = models.EmailField(unique=True)
#     full_name = models.CharField(unique=True, max_length=100)
#     otp = models.CharField(max_length=100, null=True, blank=True)
#     refresh_token = models.CharField(max_length=1000, null=True, blank=True)

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username']

#     def __str__(self):
#         return self.email
    
#     def save(self, *args, **kwargs):
#         email_username, full_name = self.email.split("@")
#         if self.full_name == "" or self.full_name == None:
#             self.full_name == email_username
#         if self.username == "" or self.username == None:
#             self.username = email_username
#         super(User, self).save(*args, **kwargs)

class User(AbstractUser):
    username = models.CharField(unique=True, max_length=100, blank=True, null=True)  # Allows null for existing users
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)  # Allows null, will populate if needed
    otp = models.CharField(max_length=100, null=True, blank=True)
    refresh_token = models.CharField(max_length=1000, null=True, blank=True)
    
    # Additional fields based on your requirements, making them nullable if they aren't strictly required
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)  # Nullable to avoid issues on existing rows
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    school_name = models.CharField(max_length=255, blank=True, null=True)
    session = models.CharField(max_length=100, blank=True, null=True)
    branch = models.CharField(max_length=100, blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    program = models.CharField(max_length=100, blank=True, null=True)
    tutoring_schedule = models.JSONField(default=dict, blank=True)  # Nullable, defaults to empty dict
    enrollment_date = models.DateField(null=True, blank=True)  # Nullable field
    amounts = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)  # Nullable and default to None
    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_relationship = models.CharField(max_length=50, blank=True, null=True)
    guardian_phone = models.CharField(max_length=15, blank=True, null=True)
    payment_plan = models.JSONField(default=list, blank=True)  # Allow multiple classes or free text
    signature = models.FileField(upload_to='signatures/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        email_username, full_name = self.email.split("@")
        if not self.full_name:
            self.full_name = email_username
        if not self.username:
            self.username = email_username
        super(User, self).save(*args, **kwargs)



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.FileField(upload_to="user_folder", default="default-user.jpg", null=True, blank=True)
    full_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.full_name:
            return str(self.full_name)
        else:
            return str(self.user.full_name)
        
    
    def save(self, *args, **kwargs):
        if self.full_name == "" or self.full_name == None:
            self.full_name == self.user.username
        super(Profile, self).save(*args, **kwargs)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)