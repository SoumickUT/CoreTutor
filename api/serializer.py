from django.contrib.auth.password_validation import validate_password
from api import models as api_models

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

from userauths.models import Profile, User

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username
        try:
            token['teacher_id'] = user.teacher.id
        except:
            token['teacher_id'] = 0


        return token

class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username
        try:
            token['teacher_id'] = user.teacher.id
        except:
            token['teacher_id'] = 0
            
        # Add admin status if both is_superuser and is_staff are True
        if user.is_superuser and user.is_staff:
            token['is_admin'] = True
        else:
            token['is_admin'] = False

        return token


class AdminSerializer(serializers.ModelSerializer):
    can_login_as_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'can_login_as_admin']
        read_only_fields = ['id', 'email', 'username', 'full_name', 'can_login_as_admin']

    def get_can_login_as_admin(self, obj):
        return obj.can_login_as_admin()

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    
# class RegisterSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
#     password2 = serializers.CharField(write_only=True, required=True)

#     class Meta:
#         model = User
#         fields = ['full_name', 'email', 'password', 'password2']

#     def validate(self, attr):
#         if attr['password'] != attr['password2']:
#             raise serializers.ValidationError({"password": "Password fields didn't match."})

#         return attr
    
#     def create(self, validated_data):
#         user = User.objects.create(
#             full_name=validated_data['full_name'],
#             email=validated_data['email'],
#         )

#         email_username, _ = user.email.split("@")
#         user.username = email_username
#         user.set_password(validated_data['password'])
#         user.save()

#         return user
    
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    phone = serializers.CharField(required=True, max_length=15)
    address = serializers.CharField(required=True, max_length=255)
    city = serializers.CharField(required=True, max_length=100)
    state = serializers.CharField(required=True, max_length=100)
    zip_code = serializers.CharField(required=True, max_length=10)
    school_name = serializers.CharField(required=True, max_length=255)
    session = serializers.CharField(required=True, max_length=100)
    branch = serializers.CharField(required=True, max_length=100)
    grade = serializers.CharField(required=True, max_length=50)
    program = serializers.CharField(required=True, max_length=100)
    tutoring_schedule = serializers.JSONField(required=True)
    enrollment_date = serializers.DateField(required=True)
    amounts = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    guardian_name = serializers.CharField(required=True, max_length=100)
    guardian_relationship = serializers.CharField(required=True, max_length=50)
    guardian_phone = serializers.CharField(required=True, max_length=15)
    
    # Dynamically populate payment plan options based on your logic
    payment_plan = serializers.CharField(required=True)  # This is now a flexible CharField.
    
    signature = serializers.FileField(required=False)

    class Meta:
        model = User
        fields = [
            'full_name', 'email', 'password', 'password2', 'phone', 'address', 'city', 'state', 'zip_code', 
            'school_name', 'session', 'branch', 'grade', 'program', 'tutoring_schedule', 'enrollment_date', 
            'amounts', 'guardian_name', 'guardian_relationship', 'guardian_phone', 'payment_plan', 'signature'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate the dynamic payment_plan (if necessary)
        # For example, you could check if it's a valid class name or if it's in a list of available classes.
        # if not self.is_valid_payment_plan(attrs['payment_plan']):
        #     raise serializers.ValidationError({"payment_plan": "Invalid payment plan."})

        return attrs

    # def is_valid_payment_plan(self, plan):
    #     # Logic to validate the dynamic plan, e.g., checking against a list of available classes or a model
    #     # Here's a dummy example, you can modify as needed
    #     available_plans = ["8 Classes", "12 Classes", "16 Classes", "24 Classes"]  # Example list
    #     return plan in available_plans
    
    def create(self, validated_data):
        # Remove the password2 field before creating the user
        password2 = validated_data.pop('password2')

        user = User.objects.create(
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            address=validated_data['address'],
            city=validated_data['city'],
            state=validated_data['state'],
            zip_code=validated_data['zip_code'],
            school_name=validated_data['school_name'],
            session=validated_data['session'],
            branch=validated_data['branch'],
            grade=validated_data['grade'],
            program=validated_data['program'],
            tutoring_schedule=validated_data['tutoring_schedule'],
            enrollment_date=validated_data['enrollment_date'],
            amounts=validated_data['amounts'],
            guardian_name=validated_data['guardian_name'],
            guardian_relationship=validated_data['guardian_relationship'],
            guardian_phone=validated_data['guardian_phone'],
            payment_plan=validated_data['payment_plan'],
            signature=validated_data.get('signature', None)
        )

        # Set username and password
        email_username, _ = user.email.split("@")
        user.username = email_username
        user.set_password(validated_data['password'])
        user.save()

        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        fields = ['id', 'title', 'image', 'slug', 'course_count']
        model = api_models.Category

class TeacherSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [ "user", "image", "full_name", "bio", "facebook", "twitter", "linkedin", "about", "country", "students", "courses", "review",]
        model = api_models.Teacher




class VariantItemSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = '__all__'
        model = api_models.VariantItem

    
    def __init__(self, *args, **kwargs):
        super(VariantItemSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3


class VariantSerializer(serializers.ModelSerializer):
    variant_items = VariantItemSerializer(many=True)
    items = VariantItemSerializer(many=True)
    class Meta:
        fields = '__all__'
        model = api_models.Variant


    def __init__(self, *args, **kwargs):
        super(VariantSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3




class Question_Answer_MessageSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False)

    class Meta:
        fields = '__all__'
        model = api_models.Question_Answer_Message


class Question_AnswerSerializer(serializers.ModelSerializer):
    messages = Question_Answer_MessageSerializer(many=True)
    profile = ProfileSerializer(many=False)
    
    class Meta:
        fields = '__all__'
        model = api_models.Question_Answer



class CartSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Cart

    def __init__(self, *args, **kwargs):
        super(CartSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3


class CartOrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.CartOrderItem

    def __init__(self, *args, **kwargs):
        super(CartOrderItemSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3


class CartOrderSerializer(serializers.ModelSerializer):
    order_items = CartOrderItemSerializer(many=True)
    
    class Meta:
        fields = '__all__'
        model = api_models.CartOrder


    def __init__(self, *args, **kwargs):
        super(CartOrderSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

class CertificateSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Certificate



# class CompletedLessonSerializer(serializers.ModelSerializer):

#     class Meta:
#         fields = '__all__'
#         model = api_models.CompletedLesson


#     def __init__(self, *args, **kwargs):
#         super(CompletedLessonSerializer, self).__init__(*args, **kwargs)
#         request = self.context.get("request")
#         if request and request.method == "POST":
#             self.Meta.depth = 0
#         else:
#             self.Meta.depth = 3

class CompletedLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.CompletedLesson
        fields = ['user_id', 'course_id', 'variant_item_id', 'date']  # Include the necessary fields

    def __init__(self, *args, **kwargs):
        super(CompletedLessonSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3


class NoteSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Note



class ReviewSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False)

    class Meta:
        fields = '__all__'
        model = api_models.Review

    def __init__(self, *args, **kwargs):
        super(ReviewSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Notification


class CouponSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Coupon


class WishlistSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Wishlist

    def __init__(self, *args, **kwargs):
        super(WishlistSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Country




class EnrolledCourseSerializer(serializers.ModelSerializer):
    lectures = VariantItemSerializer(many=True, read_only=True)
    completed_lesson = CompletedLessonSerializer(many=True, read_only=True)
    curriculum =  VariantSerializer(many=True, read_only=True)
    note = NoteSerializer(many=True, read_only=True)
    question_answer = Question_AnswerSerializer(many=True, read_only=True)
    review = ReviewSerializer(many=False, read_only=True)


    class Meta:
        fields = '__all__'
        model = api_models.EnrolledCourse

    def __init__(self, *args, **kwargs):
        super(EnrolledCourseSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

class CourseSerializer(serializers.ModelSerializer):
    students = EnrolledCourseSerializer(many=True, required=False, read_only=True,)
    curriculum = VariantSerializer(many=True, required=False, read_only=True,)
    lectures = VariantItemSerializer(many=True, required=False, read_only=True,)
    reviews = ReviewSerializer(many=True, read_only=True, required=False)
    class Meta:
        fields = ["id", "category", "teacher", "file", "image", "title", "description", "price", "language", "level", "platform_status", "teacher_course_status", "featured", "course_id", "slug", "date", "students", "curriculum", "lectures", "average_rating", "rating_count", "reviews",]
        model = api_models.Course

    def __init__(self, *args, **kwargs):
        super(CourseSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3



class StudentSummarySerializer(serializers.Serializer):
    total_courses = serializers.IntegerField(default=0)
    completed_lessons = serializers.IntegerField(default=0)
    achieved_certificates = serializers.IntegerField(default=0)

class TeacherSummarySerializer(serializers.Serializer):
    total_courses = serializers.IntegerField(default=0)
    total_students = serializers.IntegerField(default=0)
    total_revenue = serializers.IntegerField(default=0)
    monthly_revenue = serializers.IntegerField(default=0)
    

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Group
        fields = ['id', 'name']

class GroupIdField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            return super().to_internal_value(data.get('id'))
        return super().to_internal_value(data)

class QuizSerializer(serializers.ModelSerializer):
    group = GroupIdField(queryset=api_models.Group.objects.all())

    class Meta:
        model = api_models.Quizzes
        fields = ['id', 'title', 'group']


class NestedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            return super().to_internal_value(data.get('id'))
        return super().to_internal_value(data)



class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Answer
        fields = ['id', 'answer_text', 'is_right']


# class AnswerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = api_models.Answer
#         fields = ['answer_text', 'is_right']

class QuestionSerializer(serializers.ModelSerializer):
    quiz = NestedPrimaryKeyRelatedField(queryset=api_models.Quizzes.objects.all())
    answers = AnswerSerializer(many=True)

    question_type = serializers.ChoiceField(
        choices=api_models.Question.QUIZ_TYPES,
        help_text="Type of question: 'MCQ' for Multiple Choice or 'WRITING' for Writing Question."
    )

    class Meta:
        model = api_models.Question
        fields = ['id', 'title', 'quiz', 'question_type', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        question = api_models.Question.objects.create(**validated_data)
        for answer_data in answers_data:
            api_models.Answer.objects.create(question=question, **answer_data)
        return question


class NestedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            return super().to_internal_value(data.get('id'))
        return super().to_internal_value(data)
        
class WritingAnswerSerializer(serializers.ModelSerializer):
    question = NestedPrimaryKeyRelatedField(queryset=api_models.Question.objects.all())
    user = NestedPrimaryKeyRelatedField(queryset=api_models.User.objects.all())

    class Meta:
        model = api_models.WritingAnswer
        fields = ['id', 'question', 'user', 'answer_text', 'submitted_at']

        
class NestedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            return super().to_internal_value(data.get('id'))
        return super().to_internal_value(data)

class MCQAnswerSerializer(serializers.ModelSerializer):
    question = NestedPrimaryKeyRelatedField(queryset=api_models.Question.objects.all())
    user = NestedPrimaryKeyRelatedField(queryset=api_models.User.objects.all())
    selected_answer = NestedPrimaryKeyRelatedField(queryset=api_models.Answer.objects.all())

    class Meta:
        model = api_models.MCQAnswer
        fields = ['id', 'question', 'user', 'selected_answer', 'submitted_at']


        

class CreateTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Teacher
        fields = ['user', 'image', 'full_name', 'bio', 'facebook', 'twitter', 'linkedin', 'about', 'country']
    
    # Custom validation for image upload
    def validate_image(self, value):
        if value and not value.name.endswith(('.jpg', '.jpeg', '.png')):
            raise serializers.ValidationError("Image must be in .jpg, .jpeg, or .png format.")
        return value


class AdminSerializer(serializers.ModelSerializer):
    can_login_as_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'can_login_as_admin']
        read_only_fields = ['id', 'email', 'username', 'full_name', 'can_login_as_admin']

    def get_can_login_as_admin(self, obj):
        return obj.can_login_as_admin()

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['username', 'email', 'full_name', 'phone', 'address', 'city', 'state', 'zip_code', 'school_name', 'session', 'branch', 'grade', 'program', 'tutoring_schedule', 'enrollment_date', 'amounts', 'guardian_name', 'guardian_relationship', 'guardian_phone', 'payment_plan', 'signature']