from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from moviepy import VideoFileClip
import re
from userauths.models import User, Profile
from shortuuid.django_fields import ShortUUIDField
import math
import json
from django.core.exceptions import ValidationError

LANGUAGE = (
    ("English", "English"),
    ("Spanish", "Spanish"),
    ("French", "French"),
)

LEVEL = (
    ("Beginner", "Beginner"),
    ("Intemediate", "Intemediate"),
    ("Advanced", "Advanced"),
)


TEACHER_STATUS = (
    ("Draft", "Draft"),
    ("Disabled", "Disabled"),
    ("Published", "Published"),
)

PAYMENT_STATUS = (
    ("Paid", "Paid"),
    ("Processing", "Processing"),
    ("Failed", "Failed"),
)


PLATFORM_STATUS = (
    ("Review", "Review"),
    ("Disabled", "Disabled"),
    ("Rejected", "Rejected"),
    ("Draft", "Draft"),
    ("Published", "Published"),
)

RATING = (
    (1, "1 Star"),
    (2, "2 Star"),
    (3, "3 Star"),
    (4, "4 Star"),
    (5, "5 Star"),
)

NOTI_TYPE = (
    ("New Order", "New Order"),
    ("New Review", "New Review"),
    ("New Course Question", "New Course Question"),
    ("Draft", "Draft"),
    ("Course Published", "Course Published"),
    ("Course Enrollment Completed", "Course Enrollment Completed"),
)

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.FileField(upload_to="course-file", blank=True, null=True, default="default.jpg")
    full_name = models.CharField(max_length=100)
    bio = models.CharField(max_length=100, null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    twitter = models.URLField(null=True, blank=True)
    linkedin = models.URLField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.full_name
    
    def students(self):
        return CartOrderItem.objects.filter(teacher=self)
    
    def courses(self):
        return Course.objects.filter(teacher=self)
    
    def review(self):
        return Course.objects.filter(teacher=self).count()
    
class Category(models.Model):
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to="course-file", default="category.jpg", null=True, blank=True)
    active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Category"
        ordering = ['title']

    def __str__(self):
        return self.title
    
    def course_count(self):
        return Course.objects.filter(category=self).count()
    
    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.title) 
        super(Category, self).save(*args, **kwargs)
            
class Course(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    file = models.FileField(upload_to="course-file", blank=True, null=True)
    image = models.FileField(upload_to="course-file", blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    language = models.CharField(choices=LANGUAGE, default="English", max_length=100)
    level = models.CharField(choices=LEVEL, default="Beginner", max_length=100)
    platform_status = models.CharField(choices=PLATFORM_STATUS, default="Published", max_length=100)
    teacher_course_status = models.CharField(choices=TEACHER_STATUS, default="Published", max_length=100)
    featured = models.BooleanField(default=False)
    course_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    slug = models.SlugField(unique=True, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.title) + str(self.pk)
        super(Course, self).save(*args, **kwargs)

    def students(self):
        return EnrolledCourse.objects.filter(course=self)
    
    def curriculum(self):
        return Variant.objects.filter(course=self)
    
    def lectures(self):
        return VariantItem.objects.filter(variant__course=self)
    
    def average_rating(self):
        average_rating = Review.objects.filter(course=self, active=True).aggregate(avg_rating=models.Avg('rating'))
        return average_rating['avg_rating']
    
    def rating_count(self):
        return Review.objects.filter(course=self, active=True).count()
    
    def reviews(self):
        return Review.objects.filter(course=self, active=True)
    
class Variant(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000)
    variant_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
    
    def variant_items(self):
        return VariantItem.objects.filter(variant=self)
    
    def items(self):
        return VariantItem.objects.filter(variant=self)
    
    
class VariantItem(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="variant_items")
    title = models.CharField(max_length=1000)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to="course-file", null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    content_duration = models.CharField(max_length=1000, null=True, blank=True)
    preview = models.BooleanField(default=False)
    variant_item_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.variant.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file:
            clip = VideoFileClip(self.file.path)
            duration_seconds = clip.duration

            minutes, remainder = divmod(duration_seconds, 60)  

            minutes = math.floor(minutes)
            seconds = math.floor(remainder)

            duration_text = f"{minutes}m {seconds}s"
            self.content_duration = duration_text
            super().save(update_fields=['content_duration'])

class Question_Answer(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=1000, null=True, blank=True)
    qa_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    class Meta:
        ordering = ['-date']

    def messages(self):
        return Question_Answer_Message.objects.filter(question=self)
    
    def profile(self):
        return Profile.objects.get(user=self.user)
    
class Question_Answer_Message(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question = models.ForeignKey(Question_Answer, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    qam_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    qa_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    class Meta:
        ordering = ['date']

    def profile(self):
        return Profile.objects.get(user=self.user)
    
class Cart(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    tax_fee = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    country = models.CharField(max_length=100, null=True, blank=True)
    cart_id = ShortUUIDField(length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
class CartOrder(models.Model):
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teachers = models.ManyToManyField(Teacher, blank=True)
    sub_total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    tax_fee = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    initial_total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    saved = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    payment_status = models.CharField(choices=PAYMENT_STATUS, default="Processing", max_length=100)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    coupons = models.ManyToManyField("api.Coupon", blank=True)
    stripe_session_id = models.CharField(max_length=1000, null=True, blank=True)
    oid = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)


    class Meta:
        ordering = ['-date']
    
    def order_items(self):
        return CartOrderItem.objects.filter(order=self)
    
    def __str__(self):
        return self.oid
    
class CartOrderItem(models.Model):
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE, related_name="orderitem")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="order_item")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    tax_fee = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    initial_total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    saved = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    coupons = models.ManyToManyField("api.Coupon", blank=True)
    applied_coupon = models.BooleanField(default=False)
    oid = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']
    
    def order_id(self):
        return f"Order ID #{self.order.oid}"
    
    def payment_status(self):
        return f"{self.order.payment_status}"
    
    def __str__(self):
        return self.oid
    
class Certificate(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    certificate_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
class CompletedLesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    variant_item = models.ForeignKey(VariantItem, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
class EnrolledCourse(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    order_item = models.ForeignKey(CartOrderItem, on_delete=models.CASCADE)
    enrollment_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
    def lectures(self):
        return VariantItem.objects.filter(variant__course=self.course)
    
    def completed_lesson(self):
        return CompletedLesson.objects.filter(course=self.course, user=self.user)
    
    def curriculum(self):
        return Variant.objects.filter(course=self.course)
    
    def note(self):
        return Note.objects.filter(course=self.course, user=self.user)
    
    def question_answer(self):
        return Question_Answer.objects.filter(course=self.course)
    
    def review(self):
        return Review.objects.filter(course=self.course, user=self.user).first()
    
class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000, null=True, blank=True)
    note = models.TextField()
    note_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)   

    def __str__(self):
        return self.title
    
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=None)
    reply = models.CharField(null=True, blank=True, max_length=1000)
    active = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)   

    def __str__(self):
        return self.course.title
    
    def profile(self):
        return Profile.objects.get(user=self.user)
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(CartOrder, on_delete=models.SET_NULL, null=True, blank=True)
    order_item = models.ForeignKey(CartOrderItem, on_delete=models.SET_NULL, null=True, blank=True)
    review = models.ForeignKey(Review, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=100, choices=NOTI_TYPE)
    seen = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)  

    def __str__(self):
        return self.type

class Coupon(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    used_by = models.ManyToManyField(User, blank=True)
    code = models.CharField(max_length=50)
    discount = models.IntegerField(default=1)
    active = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)   

    def __str__(self):
        return self.code
    
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.course.title)
    
class Country(models.Model):
    name = models.CharField(max_length=100)
    tax_rate = models.IntegerField(default=5)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Group(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

class Subscribed(models.Model):
    name = models.CharField(max_length=254, unique=True)

    def __str__(self):
        return self.name


class Contact(models.Model):
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject



# class Quizzes(models.Model):
#     title = models.CharField(max_length=100)
#     group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="quizzes")
#     date_created = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.title

class Quizzes(models.Model):
    title = models.CharField(max_length=100)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="quizzes")
    date_created = models.DateTimeField(auto_now_add=True)
    time_limit = models.PositiveIntegerField(
        default=30, 
        help_text="Time limit for the quiz in minutes."
    )

    def __str__(self):
        return self.title
    
    


# class Question(models.Model):
#     """
#     Model representing a question in a quiz.
    
#     Choices for question types:
#     - 'MCQ' (Multiple Choice Question)
#     - 'WRITING' (Writing Question)
#     """
    
#     QUIZ_TYPES = [
#         ('MCQ', 'Multiple Choice Question'),
#         ('WRITING', 'Writing Question'),
#     ]
    
#     quiz = models.ForeignKey(Quizzes, on_delete=models.CASCADE, related_name="questions")
#     title = models.CharField(max_length=255)
#     question_type = models.CharField(
#         max_length=10,
#         choices=QUIZ_TYPES,
#         default='MCQ',
#         help_text="Type of question: 'MCQ' for Multiple Choice or 'WRITING' for Writing Question."
#     )
#     date_updated = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.title


class Question(models.Model):
    """
    Model representing a question in a quiz.
    
    Choices for question types:
    - 'MCQ' (Multiple Choice Question)
    - 'WRITING' (Writing Question)
    """
    
    QUIZ_TYPES = [
        ('MCQ', 'Multiple Choice Question'),
        ('WRITING', 'Writing Question'),
    ]
    
    quiz = models.ForeignKey(Quizzes, on_delete=models.CASCADE, related_name="questions")
    title = models.CharField(max_length=255)
    question_type = models.CharField(
        max_length=10,
        choices=QUIZ_TYPES,
        default='MCQ',
        help_text="Type of question: 'MCQ' for Multiple Choice or 'WRITING' for Writing Question."
    )
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def count_correct_answers(self):
        return self.mcq_answers.filter(selected_answer__is_right=True).count()


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    answer_text = models.CharField(max_length=255)
    is_right = models.BooleanField(default=False)

    def __str__(self):
        return self.answer_text
    
class WritingAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="writing_answers")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer_text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer by {self.user} for {self.question.title}"

class MCQAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="mcq_answers")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MCQ Answer by {self.user} for {self.question.title}"


class WritingAnswerReview(models.Model):
    """
    Model representing a teacher review for a writing answer.
    """
    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('ANSWERED', 'Answered'),
        ('CHECKED', 'Checked'),
    ]

    writing_answer = models.OneToOneField(
        WritingAnswer, 
        on_delete=models.CASCADE, 
        related_name="review"
    )
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="reviews"
    )
    availability_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='CREATED',
        help_text="Status of the answer: CREATED, ANSWERED, or CHECKED."
    )
    remarks = models.TextField(null=True, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review for {self.writing_answer} by {self.teacher}"
    

class Gallery(models.Model):
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to="gallery-file", default="gallery.jpg", null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.title
    
    
class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.FileField(upload_to="event-file", default="event.jpg", null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    create_date = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.title
    

class StudentSection(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.FileField(upload_to="student-section-file", default="student_section.jpg", null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # Allow null for now
    status = models.CharField(max_length=20, choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')], default='ACTIVE')

    def __str__(self):
        return self.title
    

class ExamSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quizzes, on_delete=models.CASCADE)
    submission_date = models.DateTimeField()
    time_taken = models.IntegerField()  # In seconds
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    score_percentage = models.FloatField()
    answers = models.TextField()  # Store answers as a JSON string

    def get_answers(self):
        """Deserialize JSON string to Python object."""
        return json.loads(self.answers)

    def set_answers(self, answers_data):
        """Serialize Python object to JSON string."""
        self.answers = json.dumps(answers_data)

    def __str__(self):
        return f"Submission by {self.user} for Quiz {self.quiz.id}"

    class Meta:
        verbose_name = "Exam Submission"
        verbose_name_plural = "Exam Submissions"
        
        
class Notice(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('academic', 'Academic'),
        ('event', 'Event'),
        ('announcement', 'Announcement'),
        ('maintenance', 'Maintenance'),
    ]

    id = models.CharField(max_length=50, primary_key=True, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    publish_date = models.DateTimeField()
    expiry_date = models.DateTimeField(null=True, blank=True)
    important = models.BooleanField(default=False)
    attachment_url = models.URLField(max_length=500, null=True, blank=True)
    attachment_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title
    

class Notice(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('academic', 'Academic'),
        ('event', 'Event'),
        ('announcement', 'Announcement'),
        ('maintenance', 'Maintenance'),
    ]

    id = models.CharField(max_length=50, primary_key=True, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    publish_date = models.DateTimeField()
    expiry_date = models.DateTimeField(null=True, blank=True)
    important = models.BooleanField(default=False)
    attachment_url = models.FileField(upload_to="notice-section-file", default="notice_section.jpg", null=True, blank=True)
    attachment_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title
    
    
######################################################

def validate_file_size(value):
    max_size = 5 * 1024 * 1024  # 5MB
    if value.size > max_size:
        raise ValidationError("File size must be less than 5MB.")

def validate_file_type(value):
    allowed_types = ['image/png', 'image/jpeg', 'image/svg+xml']
    if value.content_type not in allowed_types:
        raise ValidationError("File must be PNG, JPEG, or SVG.")

class Passage(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    time_limit = models.PositiveIntegerField(default=600)  # seconds
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class MCQQuestion(models.Model):
    passage = models.ForeignKey(Passage, related_name='mcq_questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question_text

class MCQAnswer(models.Model):
    question = models.ForeignKey(MCQQuestion, related_name='mcq_answers', on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=255)
    is_right = models.BooleanField(default=False)

    def __str__(self):
        return self.answer_text

class WrittenQuestion(models.Model):
    QUESTION_TYPES = (
        ('short', 'Short Response'),
        ('long', 'Long Response'),
        ('math_short', 'Math Short Response'),
        ('math_long', 'Math Long Response'),
    )
    passage = models.ForeignKey(Passage, related_name='written_questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    question_file = models.FileField(
        upload_to='questions/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_file_type]
    )
    question_format = models.CharField(max_length=10, choices=(('text', 'Text'), ('latex', 'LaTeX')), default='text')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    max_points = models.PositiveIntegerField()
    accepted_formats = models.JSONField(default=list)  # e.g., ["text"], ["latex", "file"]
    created_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        if self.question_type in ['short', 'math_short'] and self.max_points != 2:
            raise ValidationError("Short/math_short questions must have max_points=2.")
        if self.question_type in ['long', 'math_long'] and self.max_points != 4:
            raise ValidationError("Long/math_long questions must have max_points=4.")
        if self.question_type in ['short', 'long'] and 'file' in self.accepted_formats:
            raise ValidationError("File uploads not allowed for short/long questions.")
        if self.question_type in ['short', 'long'] and 'latex' in self.accepted_formats:
            raise ValidationError("LaTeX not allowed for short/long questions.")
        if self.question_file and 'file' not in self.accepted_formats:
            raise ValidationError("Question file not allowed for this question type.")

    def __str__(self):
        return self.question_text

class PassageSubmission(models.Model):
    passage = models.ForeignKey(Passage, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)  # MCQ score
    submission_date = models.DateTimeField(default=timezone.now)
    time_taken = models.PositiveIntegerField()

    class Meta:
        unique_together = ('passage', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.passage.title}"

class WrittenPassageSubmission(models.Model):
    passage_submission = models.OneToOneField(
        PassageSubmission,
        on_delete=models.CASCADE,
        related_name='written_passage_submission'  # Explicit reverse accessor
    )
    written_score = models.PositiveIntegerField(default=0)
    is_fully_reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Written: {self.passage_submission}"

class MCQSubmission(models.Model):
    passage_submission = models.ForeignKey(PassageSubmission, related_name='mcq_submissions', on_delete=models.CASCADE)
    question = models.ForeignKey(MCQQuestion, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(MCQAnswer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('passage_submission', 'question')

    def __str__(self):
        return f"{self.passage_submission} - {self.question}"

class WrittenSubmission(models.Model):
    written_passage_submission = models.ForeignKey(WrittenPassageSubmission, related_name='written_submissions', on_delete=models.CASCADE)
    question = models.ForeignKey(WrittenQuestion, on_delete=models.CASCADE)
    answer_text = models.TextField()
    answer_file = models.FileField(
        upload_to='submissions/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_file_type]
    )
    format = models.CharField(max_length=10, choices=(('text', 'Text'), ('latex', 'LaTeX')), default='text')
    score = models.PositiveIntegerField(null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    reviewed = models.BooleanField(default=False)
    graded_by = models.ForeignKey(Teacher, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('written_passage_submission', 'question')

    def clean(self):
        if self.question.question_type in ['short', 'long']:
            if self.format != 'text':
                raise ValidationError("Only text format allowed for short/long questions.")
            if self.answer_file:
                raise ValidationError("File uploads not allowed for short/long questions.")
            sentences = re.split(r'[.!?]+', self.answer_text.strip())
            sentences = [s.strip() for s in sentences if s.strip()]
            if self.question.question_type == 'short' and not (1 <= len(sentences) <= 3):
                raise ValidationError("Short response must have 1–3 sentences.")
            if self.question.question_type == 'long' and not (4 <= len(sentences) <= 6):
                raise ValidationError("Long response must have 4–6 sentences.")
        if self.format not in self.question.accepted_formats:
            raise ValidationError(f"Format '{self.format}' not allowed for this question.")
        if self.answer_file and 'file' not in self.question.accepted_formats:
            raise ValidationError("File upload not allowed for this question.")
        if self.score is not None:
            max_points = self.question.max_points
            if not (0 <= self.score <= max_points):
                raise ValidationError(f"Score must be between 0 and {max_points}.")

    def __str__(self):
        return f"{self.written_passage_submission} - {self.question}"
