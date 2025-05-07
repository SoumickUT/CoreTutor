from django.contrib.auth.password_validation import validate_password
from api import models as api_models

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

from userauths.models import Profile, User

# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)

#         token['full_name'] = user.full_name
#         token['email'] = user.email
#         token['username'] = user.username
#         try:
#             token['teacher_id'] = user.teacher.id
#         except:
#             token['teacher_id'] = 0


#         return token

# class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)

#         token['full_name'] = user.full_name
#         token['email'] = user.email
#         token['username'] = user.username
#         try:
#             token['teacher_id'] = user.teacher.id
#         except:
#             token['teacher_id'] = 0
            
#         # Add admin status if both is_superuser and is_staff are True
#         if user.is_superuser and user.is_staff:
#             token['is_admin'] = True
#         else:
#             token['is_admin'] = False

#         return token


# class AdminSerializer(serializers.ModelSerializer):
#     can_login_as_admin = serializers.SerializerMethodField()

#     class Meta:
#         model = User
#         fields = ['id', 'email', 'username', 'full_name', 'can_login_as_admin']
#         read_only_fields = ['id', 'email', 'username', 'full_name', 'can_login_as_admin']

#     def get_can_login_as_admin(self, obj):
#         return obj.can_login_as_admin()

# class AdminLoginSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)

#=======================03-09-205======================
# Serializers
# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#         token['full_name'] = user.full_name
#         token['email'] = user.email
#         token['username'] = user.username
#         try:
#             token['teacher_id'] = user.teacher.id
#         except:
#             token['teacher_id'] = 0
#         return token

# Custom serializer for token response
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom fields to the token payload
        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username
        try:
            token['teacher_id'] = user.teacher.id
        except:
            token['teacher_id'] = 0
        return token

    # Override the validate method to customize the response
    def validate(self, attrs):
        # Call the parent validate method to get the default token data
        data = super().validate(attrs)
        
        # Add additional user fields to the response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'username': self.user.username,
            'full_name': self.user.full_name
        }
        
        return data

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
        token['is_admin'] = user.is_superuser and user.is_staff
        return token

class AdminSerializer(serializers.ModelSerializer):
    can_login_as_admin = serializers.SerializerMethodField()

    class Meta:
        model = User  # Adjust if using a custom User model
        fields = ['id', 'email', 'username', 'full_name', 'can_login_as_admin']
        read_only_fields = ['id', 'email', 'username', 'full_name', 'can_login_as_admin']

    def get_can_login_as_admin(self, obj):
        return obj.is_superuser and obj.is_staff  # Adjust logic as needed

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
#=======================================================
    
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
    

class SubscribedSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Subscribed
        fields = ['id', 'name']

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
    group = GroupIdField(queryset=api_models.Group.objects.all())  # Handles input/output for group

    class Meta:
        model = api_models.Quizzes
        fields = ['id', 'title', 'group', 'time_limit']


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

############# 03/06/2025#################

class QuestionSerializer(serializers.ModelSerializer):
    quiz = NestedPrimaryKeyRelatedField(queryset=api_models.Quizzes.objects.all())
    answers = AnswerSerializer(many=True)
    question_type = serializers.ChoiceField(
        choices=api_models.Question.QUIZ_TYPES,
        help_text="Type of question: 'MCQ' for Multiple Choice or 'WRITING' for Writing Question."
    )
    group_id = serializers.IntegerField(source='quiz.group.id', read_only=True)  # Add group_id

    class Meta:
        model = api_models.Question
        fields = ['id', 'title', 'quiz', 'group_id', 'question_type', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        question = api_models.Question.objects.create(**validated_data)
        for answer_data in answers_data:
            api_models.Answer.objects.create(question=question, **answer_data)
        return question
    
    def update(self, instance, validated_data):
        # Handle nested answers separately
        answers_data = validated_data.pop('answers', None)
        
        # Update question fields
        instance.title = validated_data.get('title', instance.title)
        instance.quiz = validated_data.get('quiz', instance.quiz)
        instance.question_type = validated_data.get('question_type', instance.question_type)
        instance.save()

        # Handle answers if they were provided in the update
        if answers_data is not None:
            # Get existing answers
            existing_answers = {answer.id: answer for answer in instance.answers.all()}
            updated_answer_ids = []

            # Update or create answers
            for answer_data in answers_data:
                answer_id = answer_data.get('id')
                if answer_id and answer_id in existing_answers:
                    # Update existing answer
                    answer = existing_answers[answer_id]
                    for attr, value in answer_data.items():
                        setattr(answer, attr, value)
                    answer.save()
                    updated_answer_ids.append(answer_id)
                else:
                    # Create new answer
                    api_models.Answer.objects.create(question=instance, **answer_data)

            # Delete answers that weren't included in the update
            for answer_id, answer in existing_answers.items():
                if answer_id not in updated_answer_ids:
                    answer.delete()

        return instance
    
###########################################

# class QuestionSerializer(serializers.ModelSerializer):
#     quiz = NestedPrimaryKeyRelatedField(queryset=api_models.Quizzes.objects.all())
#     answers = AnswerSerializer(many=True, required=False, allow_empty=True)  # Allow empty answers

#     question_type = serializers.ChoiceField(
#         choices=api_models.Question.QUIZ_TYPES,
#         help_text="Type of question: 'MCQ' for Multiple Choice or 'WRITING' for Writing Question."
#     )

#     class Meta:
#         model = api_models.Question
#         fields = ['id', 'title', 'quiz', 'question_type', 'answers']

#     def create(self, validated_data):
#         answers_data = validated_data.pop('answers', [])  # Default to empty list if not provided
#         question = api_models.Question.objects.create(**validated_data)
#         for answer_data in answers_data:
#             api_models.Answer.objects.create(question=question, **answer_data)
#         return question

#     def update(self, instance, validated_data):
#         instance.title = validated_data.get('title', instance.title)
#         instance.quiz = validated_data.get('quiz', instance.quiz)
#         instance.question_type = validated_data.get('question_type', instance.question_type)

#         if 'answers' in validated_data:
#             answers_data = validated_data.pop('answers')
#             existing_answers = {answer.id: answer for answer in instance.answers.all()}
#             new_answers = []

#             for answer_data in answers_data:
#                 answer_id = answer_data.get('id', None)
#                 if answer_id and answer_id in existing_answers:
#                     answer = existing_answers[answer_id]
#                     answer.text = answer_data.get('text', answer.text)
#                     answer.is_correct = answer_data.get('is_correct', answer.is_correct)
#                     answer.save()
#                     del existing_answers[answer_id]
#                 else:
#                     new_answers.append(answer_data)

#             for answer in existing_answers.values():
#                 answer.delete()

#             for answer_data in new_answers:
#                 api_models.Answer.objects.create(question=instance, **answer_data)

#         instance.save()
#         return instance

class NestedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            return super().to_internal_value(data.get('id'))
        return super().to_internal_value(data)
        
# class WritingAnswerSerializer(serializers.ModelSerializer):
#     question = NestedPrimaryKeyRelatedField(queryset=api_models.Question.objects.all())
#     user = NestedPrimaryKeyRelatedField(queryset=api_models.User.objects.all())

#     class Meta:
#         model = api_models.WritingAnswer
#         fields = ['id', 'question', 'user', 'answer_text', 'submitted_at']

# class WritingAnswerSerializer(serializers.ModelSerializer):
#     question = NestedPrimaryKeyRelatedField(queryset=api_models.Question.objects.all())
#     user = NestedPrimaryKeyRelatedField(queryset=api_models.User.objects.all())

#     class Meta:
#         model = api_models.WritingAnswer
#         fields = ['id', 'question', 'user', 'answer_text', 'submitted_at']
#         read_only_fields = ['user', 'submitted_at']  # User and submitted_at are read-only

#     def create(self, validated_data):
#         # Automatically set the user from the token
#         validated_data['user'] = self.context['request'].user
#         return super().create(validated_data)

#     def update(self, instance, validated_data):
#         # Ensure user field cannot be modified during update
#         validated_data.pop('user', None)  # Ignore any user data in request
#         return super().update(instance, validated_data)

#     def validate(self, data):
#         # Optional: Ensure the authenticated user matches the instance's user (for updates)
#         request = self.context.get('request')
#         if request and self.instance and self.instance.user != request.user:
#             raise serializers.ValidationError("You can only update your own answers.")
#         return data


########################### Working ###################

# class WritingAnswerSerializer(serializers.ModelSerializer):
#     question = NestedPrimaryKeyRelatedField(queryset=api_models.Question.objects.all())
#     # Remove queryset from user since it's read-only
#     user = serializers.PrimaryKeyRelatedField(read_only=True)  # Simplified to standard DRF field

#     class Meta:
#         model = api_models.WritingAnswer
#         fields = ['id', 'question', 'user', 'answer_text', 'submitted_at']
#         read_only_fields = ['user', 'submitted_at']  # User and submitted_at are set automatically

#     def create(self, validated_data):
#         # Automatically set the user from the token
#         validated_data['user'] = self.context['request'].user
#         return super().create(validated_data)

#     def update(self, instance, validated_data):
#         # Ensure user field cannot be modified during update
#         validated_data.pop('user', None)  # Ignore any user data in request
#         return super().update(instance, validated_data)

#     def validate(self, data):
#         # Optional: Ensure the authenticated user matches the instance's user (for updates)
#         request = self.context.get('request')
#         if request and self.instance and self.instance.user != request.user:
#             raise serializers.ValidationError("You can only update your own answers.")
#         return data
        
class WritingAnswerSerializer(serializers.ModelSerializer):
    question = NestedPrimaryKeyRelatedField(queryset=api_models.Question.objects.all())
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = api_models.WritingAnswer
        fields = ['id', 'question', 'user', 'answer_text', 'submitted_at']
        read_only_fields = ['user', 'submitted_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('user', None)
        return super().update(instance, validated_data)

    def validate(self, data):
        request = self.context.get('request')
        if request and self.instance and self.instance.user != request.user:
            raise serializers.ValidationError("You can only update your own answers.")
        return data
    
class NestedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            return super().to_internal_value(data.get('id'))
        return super().to_internal_value(data)

# class MCQAnswerSerializer(serializers.ModelSerializer):
#     question = NestedPrimaryKeyRelatedField(queryset=api_models.Question.objects.all())
#     user = NestedPrimaryKeyRelatedField(queryset=api_models.User.objects.all())
#     selected_answer = NestedPrimaryKeyRelatedField(queryset=api_models.Answer.objects.all())

#     class Meta:
#         model = api_models.MCQAnswer
#         fields = ['id', 'question', 'user', 'selected_answer', 'submitted_at']

####################03-09-2025###############


# class MCQAnswerSerializer(serializers.ModelSerializer):
#     question = NestedPrimaryKeyRelatedField(queryset=api_models.Question.objects.all())
#     selected_answer = NestedPrimaryKeyRelatedField(queryset=api_models.Answer.objects.all())

#     class Meta:
#         model = api_models.MCQAnswer
#         fields = ['id', 'question', 'user', 'selected_answer', 'submitted_at']
#         read_only_fields = ['user', 'submitted_at']  # Make user read-only

#     def create(self, validated_data):
#         # Automatically set the user from the request
#         validated_data['user'] = self.context['request'].user
#         return super().create(validated_data)
        
class MCQAnswerSerializer(serializers.ModelSerializer):
    question = NestedPrimaryKeyRelatedField(queryset=api_models.Question.objects.all())
    selected_answer = NestedPrimaryKeyRelatedField(queryset=api_models.Answer.objects.all())

    class Meta:
        model = api_models.MCQAnswer
        fields = ['id', 'question', 'user', 'selected_answer', 'submitted_at']
        read_only_fields = ['user', 'submitted_at']  # User and submitted_at are read-only

    def create(self, validated_data):
        # For create: Set user from token
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # For update: Ensure user remains unchanged (from the original instance)
        validated_data.pop('user', None)  # Ignore any user data in request
        return super().update(instance, validated_data)

    def validate(self, data):
        # Optional: Ensure the authenticated user matches the instance's user (for security)
        request = self.context.get('request')
        if request and self.instance and self.instance.user != request.user:
            raise serializers.ValidationError("You can only update your own answers.")
        return data

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



class AnswerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Answer
        fields = ['id', 'answer_text', 'is_right']

class QuestionDetailSerializer(serializers.ModelSerializer):
    answers = AnswerDetailSerializer(many=True, read_only=True)  # Nested answers

    class Meta:
        model = api_models.Question
        fields = ['id', 'title', 'question_type', 'date_updated', 'answers']

class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionDetailSerializer(many=True, read_only=True)  # Nested questions

    class Meta:
        model = api_models.Quizzes
        fields = ['id', 'title', 'date_created', 'time_limit', 'questions']

class GroupDetailSerializer(serializers.ModelSerializer):
    quizzes = QuizDetailSerializer(many=True, read_only=True)  # Nested quizzes

    class Meta:
        model = api_models.Group
        fields = ['id', 'name', 'quizzes']
        

# Existing serializers (unchanged, just for reference)
class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Answer
        fields = ['id', 'answer_text', 'is_right']

class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Teacher
        fields = ['id', 'full_name']

class StudentWritingAnswerSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(source='user.username')
    question = serializers.StringRelatedField(source='question.title')
    
    class Meta:
        model = api_models.WritingAnswer
        fields = ['id', 'question', 'user', 'answer_text', 'submitted_at']

# New serializer for updating WritingAnswerReview
class WritingAnswerReviewUpdateSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(queryset=api_models.Teacher.objects.all(), required=False)

    class Meta:
        model = api_models.WritingAnswerReview
        fields = ['availability_status', 'remarks', 'checked_at', 'teacher']
        extra_kwargs = {
            'availability_status': {'required': False},
            'remarks': {'required': False},
            'checked_at': {'required': False},
            'teacher': {'required': False},
        }

    def validate(self, data):
        # Optional validation: If status is CHECKED, ensure remarks and checked_at are provided
        if data.get('availability_status') == 'CHECKED':
            if not data.get('remarks'):
                raise serializers.ValidationError("Remarks are required when status is 'CHECKED'.")
            if not data.get('checked_at'):
                raise serializers.ValidationError("Checked_at is required when status is 'CHECKED'.")
        return data

# Main serializer (unchanged except for reference)
class WritingAnswerReviewSerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    answer_details = serializers.SerializerMethodField()
    teacher_review = serializers.SerializerMethodField()

    class Meta:
        model = api_models.WritingAnswerReview
        fields = ['id', 'question', 'user', 'answer_details', 'teacher_review', 'date_updated']

    def get_question(self, obj):
        question = obj.writing_answer.question
        return {
            'question_id': question.id,
            'title': question.title,
            'question_type': question.question_type,
            'quiz_id': question.quiz.id
        }

    def get_user(self, obj):
        user = obj.writing_answer.user
        return {
            'user_id': user.id,
            'username': user.username
        }

    def get_answer_details(self, obj):
        writing_answer = obj.writing_answer
        answers = api_models.Answer.objects.filter(question=writing_answer.question)
        return {
            'answer_text': writing_answer.answer_text,
            'submitted_at': writing_answer.submitted_at,
            'availability_status': obj.availability_status,
            'question_answers': QuestionAnswerSerializer(answers, many=True).data
        }

    def get_teacher_review(self, obj):
        return {
            'remarks': obj.remarks,
            'checked_by': obj.teacher.full_name if obj.teacher else None,
            'checked_at': obj.checked_at
        }
        
        
# New Serializer
class SimpleQuestionSerializer(serializers.ModelSerializer):
    quiz = serializers.PrimaryKeyRelatedField(queryset=api_models.Quizzes.objects.all())
    question_type = serializers.ChoiceField(
        choices=api_models.Question.QUIZ_TYPES,
        help_text="Type of question: 'MCQ' for Multiple Choice or 'WRITING' for Writing Question."
    )
    group_id = serializers.IntegerField(source='quiz.group.id', read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)  # Removed source='answers'

    class Meta:
        model = api_models.Question
        fields = ['id', 'title', 'quiz', 'group_id', 'question_type', 'answers']
        
        

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Contact
        fields = ['id', 'subject', 'message', 'created_at']
        
        

# Serializer for individual answer details
class AnswerDetailUserSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    answer_type = serializers.CharField()
    answer_text = serializers.CharField()
    is_correct = serializers.BooleanField(default=False)


# serializers.py
class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Gallery
        fields = ['id', 'title', 'image', 'create_date']
        
        
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Event
        fields = ['id', 'title', 'description', 'image', 'start_date', 'end_date', 'create_date']
        
        
class StudentSectionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)
    
    class Meta:
        model = api_models.StudentSection
        fields = ['id', 'title', 'description', 'image', 'create_date', 'status', 'user']
        
class ExamSubmissionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)  # Added for retrieval
    quiz_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    score_percentage = serializers.FloatField()
    submission_date = serializers.DateTimeField()
    time_taken = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )

    def validate(self, data):
        # Validate quiz_id
        if not api_models.Quizzes.objects.filter(id=data['quiz_id']).exists():
            raise serializers.ValidationError({"quiz_id": "Invalid quiz ID"})

        # Validate user_id
        if not User.objects.filter(id=data['user_id']).exists():
            raise serializers.ValidationError({"user_id": "Invalid user ID"})

        # Validate answers
        for answer in data['answers']:
            question_id = answer.get('question')
            selected_answer_id = answer.get('selected_answer')

            # Check if question exists and is MCQ
            try:
                question = api_models.Question.objects.get(id=question_id, question_type='MCQ')
            except api_models.Question.DoesNotExist:
                raise serializers.ValidationError({
                    "answers": f"Question ID {question_id} is invalid or not an MCQ"
                })

            # Check if selected_answer exists and belongs to the question
            if not api_models.Answer.objects.filter(id=selected_answer_id, question_id=question_id).exists():
                raise serializers.ValidationError({
                    "answers": f"Selected answer ID {selected_answer_id} is invalid for question {question_id}"
                })

        return data

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        user = User.objects.get(id=validated_data['user_id'])
        quiz = api_models.Quizzes.objects.get(id=validated_data['quiz_id'])

        exam_submission = api_models.ExamSubmission(
            user=user,
            quiz=quiz,
            submission_date=validated_data['submission_date'],
            time_taken=validated_data['time_taken'],
            total_questions=validated_data['total_questions'],
            correct_answers=validated_data['correct_answers'],
            score_percentage=validated_data['score_percentage']
        )
        exam_submission.set_answers(answers_data)
        exam_submission.save()

        return exam_submission

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', None)
        instance.user = User.objects.get(id=validated_data.get('user_id', instance.user.id))
        instance.quiz = api_models.Quizzes.objects.get(id=validated_data.get('quiz_id', instance.quiz.id))
        instance.submission_date = validated_data.get('submission_date', instance.submission_date)
        instance.time_taken = validated_data.get('time_taken', instance.time_taken)
        instance.total_questions = validated_data.get('total_questions', instance.total_questions)
        instance.correct_answers = validated_data.get('correct_answers', instance.correct_answers)
        instance.score_percentage = validated_data.get('score_percentage', instance.score_percentage)
        
        if answers_data is not None:
            instance.set_answers(answers_data)
        
        instance.save()
        return instance
    
    
class NoticeSerializer(serializers.ModelSerializer):
    attachment_url = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = api_models.Notice
        fields = ['id', 'title', 'content', 'category', 'publish_date', 'expiry_date', 'important', 'attachment_url', 'attachment_name']

    def validate_attachment_url(self, value):
        if value:
            # Optional: Add file type or size validation
            allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf']
            extension = value.name.split('.')[-1].lower()
            if extension not in allowed_extensions:
                raise serializers.ValidationError("File type not allowed. Use JPG, JPEG, PNG, or PDF.")
            if value.size > 5 * 1024 * 1024:  # 5MB limit
                raise serializers.ValidationError("File size exceeds 5MB limit.")
        return value