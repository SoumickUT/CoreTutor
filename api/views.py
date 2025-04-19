from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import models
from django.db.models.functions import ExtractMonth
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from api import serializer as api_serializer
from api import models as api_models
from userauths.models import User, Profile
# In your views.py
from rest_framework import permissions
# Example usage in a view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView  # Import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
import random
from drf_yasg import openapi
from decimal import Decimal
import stripe
import requests
from datetime import datetime, timedelta
from distutils.util import strtobool
from rest_framework.exceptions import NotFound
from api.serializer import GroupSerializer, QuizSerializer, AnswerSerializer, QuestionSerializer, WritingAnswerSerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView, RetrieveAPIView

stripe.api_key = settings.STRIPE_SECRET_KEY
PAYPAL_CLIENT_ID = settings.PAYPAL_CLIENT_ID
PAYPAL_SECRET_ID = settings.PAYPAL_SECRET_ID



# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class = api_serializer.MyTokenObtainPairSerializer
    
# class AdminTokenObtainPairView(TokenObtainPairView):
#     serializer_class = api_serializer.AdminTokenObtainPairSerializer

# Token Views
# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class = api_serializer.MyTokenObtainPairSerializer

# Custom view using the serializer
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializer.MyTokenObtainPairSerializer

class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializer.AdminTokenObtainPairSerializer

# Custom Admin Login View
class AdminView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access

    def post(self, request, *args, **kwargs):
        serializer = api_serializer.AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(email=email, password=password)
            if user and user.is_superuser and user.is_staff:
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                token_serializer = api_serializer.AdminTokenObtainPairSerializer()
                token_data = token_serializer.get_token(user)

                # Serialize user data
                user_serializer = api_serializer.AdminSerializer(user)

                # Construct response
                response_data = {
                    "message": "Welcome Admin",
                    "user": user_serializer.data,
                    "access_token": str(token_data.access_token),
                    "refresh_token": str(refresh),
                }
                return Response(response_data, status=status.HTTP_200_OK)
            return Response({"detail": "Invalid credentials or not an admin."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# @csrf_exempt
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = api_serializer.RegisterSerializer

def generate_random_otp(length=7):
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = api_serializer.UserSerializer

    def get_object(self):
        email = self.kwargs['email'] # api/v1/password-email-verify/desphixs@gmail.com/

        user = User.objects.filter(email=email).first()

        if user:
            uuidb64 = user.pk
            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh.access_token)

            user.refresh_token = refresh_token
            user.otp = generate_random_otp()
            user.save()

            link = f"http://localhost:5173/create-new-password/?otp={user.otp}&uuidb64={uuidb64}&refresh_token={refresh_token}"

            context = {
                "link": link,
                "username": user.username
            }

            subject = "Password Reset Email"
            text_body = render_to_string("email/password_reset.txt", context)
            html_body = render_to_string("email/password_reset.html", context)

            msg = EmailMultiAlternatives(
                subject=subject,
                from_email=settings.FROM_EMAIL,
                to=[user.email],
                body=text_body
            )

            msg.attach_alternative(html_body, "text/html")
            msg.send()

            print("link ======", link)
        return user
    
class PasswordChangeAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = api_serializer.UserSerializer

    def create(self, request, *args, **kwargs):
        otp = request.data['otp']
        uuidb64 = request.data['uuidb64']
        password = request.data['password']

        user = User.objects.get(id=uuidb64, otp=otp)
        if user:
            user.set_password(password)
            # user.otp = ""
            user.save()

            return Response({"message": "Password Changed Successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "User Does Not Exists"}, status=status.HTTP_404_NOT_FOUND)

class ChangePasswordAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        old_password = request.data['old_password']
        new_password = request.data['new_password']

        user = User.objects.get(id=user_id)
        if user is not None:
            if check_password(old_password, user.password):
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password changed successfully", "icon": "success"})
            else:
                return Response({"message": "Old password is incorrect", "icon": "warning"})
        else:
            return Response({"message": "User does not exists", "icon": "error"})

                

class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializer.ProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = User.objects.get(id=user_id)
        return Profile.objects.get(user=user)

class CategoryListAPIView(generics.ListAPIView):
    queryset = api_models.Category.objects.filter(active=True)  
    serializer_class = api_serializer.CategorySerializer
    permission_classes = [AllowAny]

class CourseListAPIView(generics.ListAPIView):
    queryset = api_models.Course.objects.filter(platform_status="Published", teacher_course_status="Published")
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]

class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]
    queryset = api_models.Course.objects.filter(platform_status="Published", teacher_course_status="Published")

    def get_object(self):
        slug = self.kwargs['slug']
        course = api_models.Course.objects.get(slug=slug, platform_status="Published", teacher_course_status="Published")
        return course
    
# class CartAPIView(generics.CreateAPIView):
#     queryset = api_models.Cart.objects.all()
#     serializer_class = api_serializer.CartSerializer
#     permission_classes = [AllowAny]

#     def create(self, request, *args, **kwargs):
#         course_id = request.data['course_id']  
#         user_id = request.data['user_id']
#         price = request.data['price']
#         country_name = request.data['country_name']
#         cart_id = request.data['cart_id']

#         print("course_id ==========", course_id)

#         course = api_models.Course.objects.filter(id=course_id).first()
        
#         if user_id != "undefined":
#             user = User.objects.filter(id=user_id).first()
#         else:
#             user = None

#         try:
#             country_object = api_models.Country.objects.filter(name=country_name).first()
#             country = country_object.name
#         except:
#             country_object = None
#             country = "United States"

#         if country_object:
#             tax_rate = country_object.tax_rate / 100
#         else:
#             tax_rate = 0

#         cart = api_models.Cart.objects.filter(cart_id=cart_id, course=course).first()

#         if cart:
#             cart.course = course
#             cart.user = user
#             cart.price = price
#             cart.tax_fee = Decimal(price) * Decimal(tax_rate)
#             cart.country = country
#             cart.cart_id = cart_id
#             cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
#             cart.save()

#             return Response({"message": "Cart Updated Successfully"}, status=status.HTTP_200_OK)

#         else:
#             cart = api_models.Cart()

#             cart.course = course
#             cart.user = user
#             cart.price = price
#             cart.tax_fee = Decimal(price) * Decimal(tax_rate)
#             cart.country = country
#             cart.cart_id = cart_id
#             cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
#             cart.save()

#             return Response({"message": "Cart Created Successfully"}, status=status.HTTP_201_CREATED)

class CartAPIView(generics.CreateAPIView):
    queryset = api_models.Cart.objects.all()
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        required_fields = ['course_id', 'user_id', 'price', 'country_name', 'cart_id']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {"error": f"'{field}' is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        course_id = request.data['course_id']  
        user_id = request.data['user_id']
        price = request.data['price']
        country_name = request.data['country_name']
        cart_id = request.data['cart_id']

    # Existing logic follows...

        print("course_id ==========", course_id)

        course = api_models.Course.objects.filter(id=course_id).first()

        if user_id != "undefined":
            user = User.objects.filter(id=user_id).first()
        else:
            user = None

        try:
            country_object = api_models.Country.objects.filter(name=country_name).first()
            country = country_object.name
        except:
            country_object = None
            country = "United States"

        if country_object:
            tax_rate = country_object.tax_rate / 100
        else:
            tax_rate = 0

        cart = api_models.Cart.objects.filter(cart_id=cart_id, course=course).first()

        if cart:
            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.country = country
            cart.cart_id = cart_id
            cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
            cart.save()

            return Response({"message": "Cart Updated Successfully"}, status=status.HTTP_200_OK)

        else:
            cart = api_models.Cart()

            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.country = country
            cart.cart_id = cart_id
            cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
            cart.save()

            return Response({"message": "Cart Created Successfully"}, status=status.HTTP_201_CREATED)

class CartListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        queryset = api_models.Cart.objects.filter(cart_id=cart_id)
        return queryset
    
class CartListByUserAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]  # Consider using IsAuthenticated for security

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        try:
            # Ensure user_id is an integer
            user_id = int(user_id)
        except ValueError:
            raise Http404("Invalid user_id: must be an integer.")

        # Check if the user exists
        if not User.objects.filter(id=user_id).exists():
            raise Http404(f"User with id '{user_id}' does not exist.")

        # Fetch carts for the user
        queryset = api_models.Cart.objects.filter(user__id=user_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": f"No cart items found for user_id '{self.kwargs['user_id']}'."},
                status=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CartUpdateByUserAPIView(generics.UpdateAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]  # Consider IsAuthenticated

    # Define request schema
    request_body_schema = openapi.Schema(
        type=openapi.TYPE_ARRAY,
        items=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'course_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='The ID of the course', example=101),
                'price': openapi.Schema(type=openapi.TYPE_NUMBER, description='The price of the cart item', example=49.00),
                'country_name': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the country', example='United States'),
                'cart_id': openapi.Schema(type=openapi.TYPE_STRING, description='A unique identifier for the cart (optional)', example='123456'),
            },
            required=['course_id', 'price', 'country_name'],
        ),
        min_items=1,
        description='A list of cart items to add or update'
    )

    # Define response schemas
    success_response_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, enum=['Cart item added successfully', 'Cart item updated successfully']),
                        'cart': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'course': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                                'user': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                                'price': openapi.Schema(type=openapi.TYPE_STRING),
                                'tax_fee': openapi.Schema(type=openapi.TYPE_STRING),
                                'total': openapi.Schema(type=openapi.TYPE_STRING),
                                'country': openapi.Schema(type=openapi.TYPE_STRING),
                                'cart_id': openapi.Schema(type=openapi.TYPE_STRING),
                                'date': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            }
                        ),
                    }
                )
            ),
            'errors': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'index': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
        }
    )

    @swagger_auto_schema(
        operation_summary="Update or Add Multiple Cart Items by User ID",
        operation_description="Add or update multiple cart items for a user identified by user_id. Each item in the request array represents a cart item.",
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description='ID of the user whose cart is being updated',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        request_body=request_body_schema,
        responses={
            200: openapi.Response(
                description='All items processed successfully',
                schema=success_response_schema,
                examples={
                    'application/json': {
                        'results': [
                            {
                                'message': 'Cart item added successfully',
                                'cart': {
                                    'id': 1,
                                    'course': {'id': 101, 'title': 'Python Basics'},
                                    'user': {'id': 1, 'username': 'testuser'},
                                    'price': '49.00',
                                    'tax_fee': '5.00',
                                    'total': '54.00',
                                    'country': 'United States',
                                    'cart_id': '123456',
                                    'date': '2025-04-09T04:34:22.784Z',
                                },
                            },
                        ],
                        'errors': [],
                    }
                }
            ),
            207: openapi.Response(
                description='Mixed success and errors',
                schema=success_response_schema,
                examples={
                    'application/json': {
                        'results': [
                            {
                                'message': 'Cart item added successfully',
                                'cart': {
                                    'id': 1,
                                    'course': {'id': 101, 'title': 'Python Basics'},
                                    'user': {'id': 1, 'username': 'testuser'},
                                    'price': '49.00',
                                    'tax_fee': '5.00',
                                    'total': '54.00',
                                    'country': 'United States',
                                    'cart_id': '123456',
                                    'date': '2025-04-09T04:34:22.784Z',
                                },
                            },
                        ],
                        'errors': [
                            {'index': 1, 'error': "Course with id '999' does not exist."},
                        ],
                    }
                }
            ),
            400: openapi.Response(description='Bad Request - Invalid input'),
            404: openapi.Response(description='Not Found - Invalid user_id or user does not exist'),
        },
    )
    def update(self, request, *args, **kwargs):
        user_id = self.kwargs['user_id']
        
        # Validate user_id
        try:
            user_id = int(user_id)
        except ValueError:
            raise Http404("Invalid user_id: must be an integer.")
        
        if not User.objects.filter(id=user_id).exists():
            raise Http404(f"User with id '{user_id}' does not exist.")

        # Expect a list of items
        if not isinstance(request.data, list):
            return Response(
                {"error": "Request body must be a list of cart items."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.get(id=user_id)
        results = []
        errors = []

        for index, item in enumerate(request.data):
            # Validate required fields
            required_fields = ['course_id', 'price', 'country_name']
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                errors.append({
                    "index": index,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                })
                continue

            course_id = item['course_id']
            price = item['price']
            country_name = item['country_name']
            cart_id = item.get('cart_id', None)

            # Validate course_id
            try:
                course_id = int(course_id)
                course = api_models.Course.objects.filter(id=course_id).first()
                if not course:
                    errors.append({
                        "index": index,
                        "error": f"Course with id '{course_id}' does not exist."
                    })
                    continue
            except ValueError:
                errors.append({
                    "index": index,
                    "error": "'course_id' must be a valid integer."
                })
                continue

            # Validate price
            try:
                price = Decimal(price)
            except (ValueError, TypeError):
                errors.append({
                    "index": index,
                    "error": "'price' must be a valid number."
                })
                continue

            # Handle country and tax
            country_object = api_models.Country.objects.filter(name=country_name).first()
            country = country_object.name if country_object else "United States"
            tax_rate = country_object.tax_rate / 100 if country_object else 0
            tax_fee = price * Decimal(tax_rate)
            total = price + tax_fee

            # Check if cart item exists
            cart = api_models.Cart.objects.filter(user__id=user_id, course=course).first()

            if cart:
                # Update existing cart item
                cart.price = price
                cart.tax_fee = tax_fee
                cart.total = total
                cart.country = country
                cart.save()
                serializer = self.get_serializer(cart)
                results.append({
                    "message": "Cart item updated successfully",
                    "cart": serializer.data
                })
            else:
                # Create new cart item
                cart = api_models.Cart(
                    course=course,
                    user=user,
                    price=price,
                    tax_fee=tax_fee,
                    total=total,
                    country=country,
                    cart_id=cart_id if cart_id else api_models.Cart._meta.get_field('cart_id').default(),
                )
                cart.save()
                serializer = self.get_serializer(cart)
                results.append({
                    "message": "Cart item added successfully",
                    "cart": serializer.data
                })

        response_data = {"results": results}
        if errors:
            response_data["errors"] = errors
            status_code = status.HTTP_207_MULTI_STATUS if results else status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_200_OK

        return Response(response_data, status=status_code)
    
class CartUpdateByCartAndUserAPIView(generics.UpdateAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]  # Consider IsAuthenticated

    # Define request schema
    request_body_schema = openapi.Schema(
        type=openapi.TYPE_ARRAY,
        items=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'course_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='The ID of the course', example=101),
                'price': openapi.Schema(type=openapi.TYPE_NUMBER, description='The price of the cart item', example=49.00),
                'country_name': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the country', example='United States'),
            },
            required=['course_id', 'price', 'country_name'],
        ),
        min_items=1,
        description='A list of cart items to add or update under the specified cart_id and user_id'
    )

    # Define response schema
    success_response_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, enum=['Cart item added successfully', 'Cart item updated successfully']),
                        'cart': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'course': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                                'user': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                                'price': openapi.Schema(type=openapi.TYPE_STRING),
                                'tax_fee': openapi.Schema(type=openapi.TYPE_STRING),
                                'total': openapi.Schema(type=openapi.TYPE_STRING),
                                'country': openapi.Schema(type=openapi.TYPE_STRING),
                                'cart_id': openapi.Schema(type=openapi.TYPE_STRING),
                                'date': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            }
                        ),
                    }
                )
            ),
            'errors': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'index': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
        }
    )

    @swagger_auto_schema(
        operation_summary="Update or Add Cart Items by Cart ID and User ID",
        operation_description="Add or update cart items for a specific cart_id and user_id. Each item in the request array is processed under the specified cart_id.",
        manual_parameters=[
            openapi.Parameter(
                'cart_id',
                openapi.IN_PATH,
                description='The unique identifier of the cart',
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description='ID of the user whose cart is being updated',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        request_body=request_body_schema,
        responses={
            200: openapi.Response(
                description='All items processed successfully',
                schema=success_response_schema,
                examples={
                    'application/json': {
                        'results': [
                            {
                                'message': 'Cart item added successfully',
                                'cart': {
                                    'id': 1,
                                    'course': {'id': 101, 'title': 'Python Basics'},
                                    'user': {'id': 1, 'username': 'testuser'},
                                    'price': '49.00',
                                    'tax_fee': '5.00',
                                    'total': '54.00',
                                    'country': 'United States',
                                    'cart_id': '123456',
                                    'date': '2025-04-09T04:34:22.784Z',
                                },
                            },
                        ],
                        'errors': [],
                    }
                }
            ),
            207: openapi.Response(
                description='Mixed success and errors',
                schema=success_response_schema,
                examples={
                    'application/json': {
                        'results': [
                            {
                                'message': 'Cart item added successfully',
                                'cart': {
                                    'id': 1,
                                    'course': {'id': 101, 'title': 'Python Basics'},
                                    'user': {'id': 1, 'username': 'testuser'},
                                    'price': '49.00',
                                    'tax_fee': '5.00',
                                    'total': '54.00',
                                    'country': 'United States',
                                    'cart_id': '123456',
                                    'date': '2025-04-09T04:34:22.784Z',
                                },
                            },
                        ],
                        'errors': [
                            {'index': 1, 'error': "Course with id '999' does not exist."},
                        ],
                    }
                }
            ),
            400: openapi.Response(description='Bad Request - Invalid input'),
            404: openapi.Response(description='Not Found - Invalid user_id or user does not exist'),
        },
    )
    def update(self, request, *args, **kwargs):
        user_id = self.kwargs['user_id']
        cart_id = self.kwargs['cart_id']

        # Validate user_id
        try:
            user_id = int(user_id)
        except ValueError:
            raise Http404("Invalid user_id: must be an integer.")
        
        if not User.objects.filter(id=user_id).exists():
            raise Http404(f"User with id '{user_id}' does not exist.")

        # Validate cart_id (basic check for non-empty string)
        if not cart_id or not isinstance(cart_id, str):
            return Response(
                {"error": "Invalid cart_id: must be a non-empty string."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Expect a list of items
        if not isinstance(request.data, list):
            return Response(
                {"error": "Request body must be a list of cart items."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.get(id=user_id)
        results = []
        errors = []

        for index, item in enumerate(request.data):
            # Validate required fields
            required_fields = ['course_id', 'price', 'country_name']
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                errors.append({
                    "index": index,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                })
                continue

            course_id = item['course_id']
            price = item['price']
            country_name = item['country_name']

            # Validate course_id
            try:
                course_id = int(course_id)
                course = api_models.Course.objects.filter(id=course_id).first()
                if not course:
                    errors.append({
                        "index": index,
                        "error": f"Course with id '{course_id}' does not exist."
                    })
                    continue
            except ValueError:
                errors.append({
                    "index": index,
                    "error": "'course_id' must be a valid integer."
                })
                continue

            # Validate price
            try:
                price = Decimal(price)
            except (ValueError, TypeError):
                errors.append({
                    "index": index,
                    "error": "'price' must be a valid number."
                })
                continue

            # Handle country and tax
            country_object = api_models.Country.objects.filter(name=country_name).first()
            country = country_object.name if country_object else "United States"
            tax_rate = country_object.tax_rate / 100 if country_object else 0
            tax_fee = price * Decimal(tax_rate)
            total = price + tax_fee

            # Check if cart item exists with the given cart_id and course
            cart = api_models.Cart.objects.filter(cart_id=cart_id, user__id=user_id, course=course).first()

            if cart:
                # Update existing cart item
                cart.price = price
                cart.tax_fee = tax_fee
                cart.total = total
                cart.country = country
                cart.save()
                serializer = self.get_serializer(cart)
                results.append({
                    "message": "Cart item updated successfully",
                    "cart": serializer.data
                })
            else:
                # Create new cart item
                cart = api_models.Cart(
                    course=course,
                    user=user,
                    price=price,
                    tax_fee=tax_fee,
                    total=total,
                    country=country,
                    cart_id=cart_id,  # Use the provided cart_id from URL
                )
                cart.save()
                serializer = self.get_serializer(cart)
                results.append({
                    "message": "Cart item added successfully",
                    "cart": serializer.data
                })

        response_data = {"results": results}
        if errors:
            response_data["errors"] = errors
            status_code = status.HTTP_207_MULTI_STATUS if results else status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_200_OK

        return Response(response_data, status=status_code)

class CartItemDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        cart_id = self.kwargs['cart_id']
        item_id = self.kwargs['item_id']

        return api_models.Cart.objects.filter(cart_id=cart_id, id=item_id).first()

class CartStatsAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]
    lookup_field = 'cart_id'

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        queryset = api_models.Cart.objects.filter(cart_id=cart_id)
        return queryset
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        total_price = 0.00
        total_tax = 0.00
        total_total = 0.00

        for cart_item in queryset:
            total_price += float(self.calculate_price(cart_item))
            total_tax += float(self.calculate_tax(cart_item))
            total_total += round(float(self.calculate_total(cart_item)), 2)

        data = {
            "price": total_price,
            "tax": total_tax,
            "total": total_total,
        }

        return Response(data)

    def calculate_price(self, cart_item):
        return cart_item.price
    
    def calculate_tax(self, cart_item):
        return cart_item.tax_fee

    def calculate_total(self, cart_item):
        return cart_item.total
    


class CartStatsByUserAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]  # Adjust permissions as needed (e.g., IsAuthenticated)

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        queryset = api_models.Cart.objects.filter(user__id=user_id)
        return queryset
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        total_price = 0.00
        total_tax = 0.00
        total_total = 0.00

        for cart_item in queryset:
            total_price += float(self.calculate_price(cart_item))
            total_tax += float(self.calculate_tax(cart_item))
            total_total += round(float(self.calculate_total(cart_item)), 2)

        data = {
            "price": total_price,
            "tax": total_tax,
            "total": total_total,
        }

        return Response(data)

    def calculate_price(self, cart_item):
        return cart_item.price
    
    def calculate_tax(self, cart_item):
        return cart_item.tax_fee

    def calculate_total(self, cart_item):
        return cart_item.total


class CreateOrderAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.CartOrderSerializer
    permission_classes = [AllowAny]
    queryset = api_models.CartOrder.objects.all()
    
    def create(self, request, *args, **kwargs):
        required_fields = ['full_name', 'email', 'country', 'cart_id']
        for field in required_fields:
            if field not in request.data or not request.data[field]:
                return Response(
                    { "error": f"{field} is required." },
                    status=status.HTTP_400_BAD_REQUEST
                )

        full_name = request.data['full_name']
        email = request.data['email']
        country = request.data['country']
        cart_id = request.data['cart_id']
        user_id = request.data.get('user_id')

        if user_id and user_id != 'undefined':
            try:
                user = User.objects.get(id=int(user_id))
                print('User ',user)
                print('User Id ',user_id)
            except (ValueError, User.DoesNotExist):
                user = None
        else:
            user = None

        cart_items = api_models.Cart.objects.filter(cart_id=cart_id)

        total_price = Decimal(0.00)
        total_tax = Decimal(0.00)
        total_initial_total = Decimal(0.00)
        total_total = Decimal(0.00)

        order = api_models.CartOrder.objects.create(
            full_name=full_name,
            email=email,
            country=country,
            student=user
        )

        for c in cart_items:
            api_models.CartOrderItem.objects.create(
                order=order,
                course=c.course,
                price=c.price,
                tax_fee=c.tax_fee,
                total=c.total,
                initial_total=c.total,
                teacher=c.course.teacher
            )

            total_price += Decimal(c.price)
            total_tax += Decimal(c.tax_fee)
            total_initial_total += Decimal(c.total)
            total_total += Decimal(c.total)

            order.teachers.add(c.course.teacher)

        order.sub_total = total_price
        order.tax_fee = total_tax
        order.initial_total = total_initial_total
        order.total = total_total
        order.save()

        return Response({"message": "Order Created Successfully", "order_oid": order.oid}, status=status.HTTP_201_CREATED)

    # def create(self, request, *args, **kwargs):
    #     full_name = request.data['full_name']
    #     email = request.data['email']
    #     country = request.data['country']
    #     cart_id = request.data['cart_id']
    #     user_id = request.data['user_id']

    #     if user_id != 0:
    #         user = User.objects.get(id=user_id)
    #     else:
    #         user = None

    #     cart_items = api_models.Cart.objects.filter(cart_id=cart_id)

    #     total_price = Decimal(0.00)
    #     total_tax = Decimal(0.00)
    #     total_initial_total = Decimal(0.00)
    #     total_total = Decimal(0.00)

    #     order = api_models.CartOrder.objects.create(
    #         full_name=full_name,
    #         email=email,
    #         country=country,
    #         student=user
    #     )

    #     for c in cart_items:
    #         api_models.CartOrderItem.objects.create(
    #             order=order,
    #             course=c.course,
    #             price=c.price,
    #             tax_fee=c.tax_fee,
    #             total=c.total,
    #             initial_total=c.total,
    #             teacher=c.course.teacher
    #         )

    #         total_price += Decimal(c.price)
    #         total_tax += Decimal(c.tax_fee)
    #         total_initial_total += Decimal(c.total)
    #         total_total += Decimal(c.total)

    #         order.teachers.add(c.course.teacher)

    #     order.sub_total = total_price
    #     order.tax_fee = total_tax
    #     order.initial_total = total_initial_total
    #     order.total = total_total
    #     order.save()

    #     return Response({"message": "Order Created Successfully", "order_oid": order.oid}, status=status.HTTP_201_CREATED)



class CheckoutAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CartOrderSerializer
    permission_classes = [AllowAny]
    queryset = api_models.CartOrder.objects.all()
    lookup_field = 'oid'


class CouponApplyAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.CouponSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        order_oid = request.data['order_oid']
        coupon_code = request.data['coupon_code']

        order = api_models.CartOrder.objects.get(oid=order_oid)
        coupon = api_models.Coupon.objects.get(code=coupon_code)

        if coupon:
            order_items = api_models.CartOrderItem.objects.filter(order=order, teacher=coupon.teacher)
            for i in order_items:
                if not coupon in i.coupons.all():
                    discount = i.total * coupon.discount / 100

                    i.total -= discount
                    i.price -= discount
                    i.saved += discount
                    i.applied_coupon = True
                    i.coupons.add(coupon)

                    order.coupons.add(coupon)
                    order.total -= discount
                    order.sub_total -= discount
                    order.saved += discount

                    i.save()
                    order.save()
                    coupon.used_by.add(order.student)
                    return Response({"message": "Coupon Found and Activated", "icon": "success"}, status=status.HTTP_201_CREATED)
                else:
                    return Response({"message": "Coupon Already Applied", "icon": "warning"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Coupon Not Found", "icon": "error"}, status=status.HTTP_404_NOT_FOUND)

class StripeCheckoutAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.CartOrderSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        
        order_oid = self.kwargs['order_oid']
        order = api_models.CartOrder.objects.get(oid=order_oid)

        if not order:
            return Response({"message": "Order Not Found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email = order.email,
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': order.full_name,
                            },
                            'unit_amount': int(order.total * 100)
                        },
                        'quantity': 1
                    }
                ],
                mode='payment',
                success_url=settings.FRONTEND_SITE_URL + '/payment-success/' + order.oid + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url= settings.FRONTEND_SITE_URL + '/payment-failed/'
            )
            print("checkout_session ====", checkout_session)
            order.stripe_session_id = checkout_session.id

            return redirect(checkout_session.url)
        except stripe.error.StripeError as e:
            return Response({"message": f"Something went wrong when trying to make payment. Error: {str(e)}"})


def get_access_token(client_id, secret_key):
    token_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    data = {'grant_type': 'client_credentials'}
    auth = (client_id, secret_key)
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        print("Access TOken ====", response.json()['access_token'])
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to get access token from paypal {response.status_code}")
    

class PaymentSuccessAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny] #Test
    serializer_class = api_serializer.CartOrderSerializer
    queryset = api_models.CartOrder.objects.all()

    def create(self, request, *args, **kwargs):
        order_oid = request.data['order_oid']
        session_id = request.data['session_id']
        paypal_order_id = request.data['paypal_order_id']

        order = api_models.CartOrder.objects.get(oid=order_oid)
        order_items = api_models.CartOrderItem.objects.filter(order=order)


        # Paypal payment success
        if paypal_order_id != "null":
            paypal_api_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {get_access_token(PAYPAL_CLIENT_ID, PAYPAL_SECRET_ID)}"
            }
            response = requests.get(paypal_api_url, headers=headers)
            if response.status_code == 200:
                paypal_order_data = response.json()
                paypal_payment_status = paypal_order_data['status']
                if paypal_payment_status == "COMPLETED":
                    if order.payment_status == "Processing":
                        order.payment_status = "Paid"
                        order.save()
                        api_models.Notification.objects.create(user=order.student, order=order, type="Course Enrollment Completed")

                        for o in order_items:
                            api_models.Notification.objects.create(
                                teacher=o.teacher,
                                order=order,
                                order_item=o,
                                type="New Order",
                            )
                            api_models.EnrolledCourse.objects.create(
                                course=o.course,
                                user=order.student,
                                teacher=o.teacher,
                                order_item=o
                            )

                        return Response({"message": "Payment Successfull"})
                    else:
                        return Response({"message": "Already Paid"})
                else:
                    return Response({"message": "Payment Failed"})
            else:
                return Response({"message": "PayPal Error Occured"})


        # Stripe payment success
        if session_id != 'null':
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                if order.payment_status == "Processing":
                    order.payment_status = "Paid"
                    order.save()

                    api_models.Notification.objects.create(user=order.student, order=order, type="Course Enrollment Completed")
                    for o in order_items:
                        api_models.Notification.objects.create(
                            teacher=o.teacher,
                            order=order,
                            order_item=o,
                            type="New Order",
                        )
                        api_models.EnrolledCourse.objects.create(
                            course=o.course,
                            user=order.student,
                            teacher=o.teacher,
                            order_item=o
                        )
                    return Response({"message": "Payment Successfull"})
                else:
                    return Response({"message": "Already Paid"})
            else:
                    return Response({"message": "Payment Failed"})
            
class SearchCourseAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.GET.get('query')
        # learn lms
        return api_models.Course.objects.filter(title__icontains=query, platform_status="Published", teacher_course_status="Published")
    




class StudentSummaryAPIView(generics.ListAPIView):
    serializer_class = api_serializer.StudentSummarySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = User.objects.get(id=user_id)

        total_courses = api_models.EnrolledCourse.objects.filter(user=user).count()
        completed_lessons = api_models.CompletedLesson.objects.filter(user=user).count()
        achieved_certificates = api_models.Certificate.objects.filter(user=user).count()

        return [{
            "total_courses": total_courses,
            "completed_lessons": completed_lessons,
            "achieved_certificates": achieved_certificates,
        }]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class StudentCourseListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.EnrolledCourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user =  User.objects.get(id=user_id)
        return api_models.EnrolledCourse.objects.filter(user=user)
    

class StudentCourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.EnrolledCourseSerializer
    permission_classes = [AllowAny]
    lookup_field = 'enrollment_id'

    def get_object(self):
        user_id = self.kwargs['user_id']
        enrollment_id = self.kwargs['enrollment_id']

        user = User.objects.get(id=user_id)
        return api_models.EnrolledCourse.objects.get(user=user, enrollment_id=enrollment_id)
         
class StudentCourseCompletedCreateAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.CompletedLessonSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # Get required fields from the request data
        user_id = request.data.get('user_id')
        course_id = request.data.get('course_id')
        variant_item_id = request.data.get('variant_item_id')
        date = request.data.get('date')  # Ensure that 'date' is also part of the request body

        # Ensure all required fields are present
        if not all([user_id, course_id, variant_item_id, date]):
            raise ValidationError({"error": "user_id, course_id, variant_item_id, and date are required fields."})

        # Fetch corresponding objects from the database
        try:
            user = User.objects.get(id=user_id)
            course = api_models.Course.objects.get(id=course_id)
            variant_item = api_models.VariantItem.objects.get(variant_item_id=variant_item_id)
        except User.DoesNotExist:
            raise ValidationError({"error": "User with the given ID does not exist."})
        except api_models.Course.DoesNotExist:
            raise ValidationError({"error": "Course with the given ID does not exist."})
        except api_models.VariantItem.DoesNotExist:
            raise ValidationError({"error": "VariantItem with the given ID does not exist."})

        # Check if the lesson is already marked as completed
        completed_lessons = api_models.CompletedLesson.objects.filter(
            user=user, course=course, variant_item=variant_item).first()

        if completed_lessons:
            # If already marked as completed, delete it
            completed_lessons.delete()
            return Response({
                "message": "Course marked as not completed",
                "user_id": user_id,
                "course_id": course_id,
                "variant_item_id": variant_item_id,
                "date": date
            })

        # Create a new completed lesson if not already marked
        api_models.CompletedLesson.objects.create(
            user=user, course=course, variant_item=variant_item, date=date
        )

        return Response({
            "message": "Course marked as completed",
            "user_id": user_id,
            "course_id": course_id,
            "variant_item_id": variant_item_id,
            "date": date
        })

    
class StudentNoteCreateAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializer.NoteSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        enrollment_id = self.kwargs['enrollment_id']

        user = User.objects.get(id=user_id)
        enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)
        
        return api_models.Note.objects.filter(user=user, course=enrolled.course)

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        enrollment_id = request.data['enrollment_id']
        title = request.data['title']
        note = request.data['note']

        user = User.objects.get(id=user_id)
        enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)
        
        api_models.Note.objects.create(user=user, course=enrolled.course, note=note, title=title)

        return Response({"message": "Note created successfullly"}, status=status.HTTP_201_CREATED)
    

class StudentNoteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = api_serializer.NoteSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs['user_id']
        enrollment_id = self.kwargs['enrollment_id']
        note_id = self.kwargs['note_id']

        user = User.objects.get(id=user_id)
        enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)
        note = api_models.Note.objects.get(user=user, course=enrolled.course, id=note_id)
        return note


class StudentRateCourseCreateAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.ReviewSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        course_id = request.data['course_id']
        rating = request.data['rating']
        review = request.data['review']

        user = User.objects.get(id=user_id)
        course = api_models.Course.objects.get(id=course_id)

        api_models.Review.objects.create(
            user=user,
            course=course,
            review=review,
            rating=rating,
            active=True,
        )

        return Response({"message": "Review created successfullly"}, status=status.HTTP_201_CREATED)


class StudentRateCourseUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializer.ReviewSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs['user_id']
        review_id = self.kwargs['review_id']

        user = User.objects.get(id=user_id)
        return api_models.Review.objects.get(id=review_id, user=user)
    

class StudentWishListListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializer.WishlistSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = User.objects.get(id=user_id)
        return api_models.Wishlist.objects.filter(user=user)
    
    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        course_id = request.data['course_id']

        user = User.objects.get(id=user_id)
        course = api_models.Course.objects.get(id=course_id)

        wishlist = api_models.Wishlist.objects.filter(user=user, course=course).first()
        if wishlist:
            wishlist.delete()
            return Response({"message": "Wishlist Deleted"}, status=status.HTTP_200_OK)
        else:
            api_models.Wishlist.objects.create(
                user=user, course=course
            )
            return Response({"message": "Wishlist Created"}, status=status.HTTP_201_CREATED)



class QuestionAnswerListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializer.Question_AnswerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course = api_models.Course.objects.get(id=course_id)
        return api_models.Question_Answer.objects.filter(course=course)
    
    def create(self, request, *args, **kwargs):
        course_id = request.data['course_id']
        user_id = request.data['user_id']
        title = request.data['title']
        message = request.data['message']

        user = User.objects.get(id=user_id)
        course = api_models.Course.objects.get(id=course_id)
        
        question = api_models.Question_Answer.objects.create(
            course=course,
            user=user,
            title=title
        )

        api_models.Question_Answer_Message.objects.create(
            course=course,
            user=user,
            message=message,
            question=question
        )
        
        return Response({"message": "Group conversation Started"}, status=status.HTTP_201_CREATED)


class QuestionAnswerMessageSendAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.Question_Answer_MessageSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        course_id = request.data['course_id']
        qa_id = request.data['qa_id']
        user_id = request.data['user_id']
        message = request.data['message']

        user = User.objects.get(id=user_id)
        course = api_models.Course.objects.get(id=course_id)
        question = api_models.Question_Answer.objects.get(qa_id=qa_id)
        api_models.Question_Answer_Message.objects.create(
            course=course,
            user=user,
            message=message,
            question=question
        )

        question_serializer = api_serializer.Question_AnswerSerializer(question)
        return Response({"messgae": "Message Sent", "question": question_serializer.data})




class TeacherSummaryAPIView(generics.ListAPIView):
    serializer_class = api_serializer.TeacherSummarySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)

        one_month_ago = datetime.today() - timedelta(days=28)

        total_courses = api_models.Course.objects.filter(teacher=teacher).count()
        total_revenue = api_models.CartOrderItem.objects.filter(teacher=teacher, order__payment_status="Paid").aggregate(total_revenue=models.Sum("price"))['total_revenue'] or 0
        monthly_revenue = api_models.CartOrderItem.objects.filter(teacher=teacher, order__payment_status="Paid", date__gte=one_month_ago).aggregate(total_revenue=models.Sum("price"))['total_revenue'] or 0

        enrolled_courses = api_models.EnrolledCourse.objects.filter(teacher=teacher)
        unique_student_ids = set()
        students = []

        for course in enrolled_courses:
            if course.user_id not in unique_student_ids:
                user = User.objects.get(id=course.user_id)
                student = {
                    "full_name": user.profile.full_name,
                    "image": user.profile.image.url,
                    "country": user.profile.country,
                    "date": course.date
                }

                students.append(student)
                unique_student_ids.add(course.user_id)

        return [{
            "total_courses": total_courses,
            "total_revenue": total_revenue,
            "monthly_revenue": monthly_revenue,
            "total_students": len(students),
        }]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

class TeacherCourseListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Course.objects.filter(teacher=teacher)
    

class TeacherReviewListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Review.objects.filter(course__teacher=teacher)
    

class TeacherReviewDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializer.ReviewSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        review_id = self.kwargs['review_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Review.objects.get(course__teacher=teacher, id=review_id)
    

class TeacherStudentsListAPIVIew(viewsets.ViewSet):
    
    def list(self, request, teacher_id=None):
        teacher = api_models.Teacher.objects.get(id=teacher_id)

        enrolled_courses = api_models.EnrolledCourse.objects.filter(teacher=teacher)
        unique_student_ids = set()
        students = []

        for course in enrolled_courses:
            if course.user_id not in unique_student_ids:
                user = User.objects.get(id=course.user_id)
                student = {
                    "full_name": user.profile.full_name,
                    "image": user.profile.image.url,
                    "country": user.profile.country,
                    "date": course.date
                }

                students.append(student)
                unique_student_ids.add(course.user_id)

        return Response(students)
    

@api_view(("GET", ))
def TeacherAllMonthEarningAPIView(request, teacher_id):
    teacher = api_models.Teacher.objects.get(id=teacher_id)
    monthly_earning_tracker = (
        api_models.CartOrderItem.objects
        .filter(teacher=teacher, order__payment_status="Paid")
        .annotate(
            month=ExtractMonth("date")
        )
        .values("month")
        .annotate(
            total_earning=models.Sum("price")
        )
        .order_by("month")
    )

    return Response(monthly_earning_tracker)

class TeacherBestSellingCourseAPIView(viewsets.ViewSet):

    def list(self, request, teacher_id=None):
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        courses_with_total_price = []
        courses = api_models.Course.objects.filter(teacher=teacher)

        for course in courses:
            revenue = course.enrolledcourse_set.aggregate(total_price=models.Sum('order_item__price'))['total_price'] or 0
            sales = course.enrolledcourse_set.count()

            courses_with_total_price.append({
                'course_image': course.image.url,
                'course_title': course.title,
                'revenue': revenue,
                'sales': sales,
            })

        return Response(courses_with_total_price)
    
class TeacherCourseOrdersListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CartOrderItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)

        return api_models.CartOrderItem.objects.filter(teacher=teacher)

class TeacherQuestionAnswerListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.Question_AnswerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Question_Answer.objects.filter(course__teacher=teacher)
    
class TeacherCouponListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializer.CouponSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Coupon.objects.filter(teacher=teacher)
    
class TeacherCouponDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = api_serializer.CouponSerializer
    permission_classes = [AllowAny]
    
    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        coupon_id = self.kwargs['coupon_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Coupon.objects.get(teacher=teacher, id=coupon_id)
    
class TeacherNotificationListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Notification.objects.filter(teacher=teacher, seen=False)
    
class TeacherNotificationDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializer.NotificationSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        noti_id = self.kwargs['noti_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Notification.objects.get(teacher=teacher, id=noti_id)
    
class CourseCreateAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access
    querysect = api_models.Course.objects.all()
    serializer_class = api_serializer.CourseSerializer
    permisscion_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        course_instance = serializer.save()

        variant_data = []
        for key, value in self.request.data.items():
            if key.startswith('variant') and '[variant_title]' in key:
                index = key.split('[')[1].split(']')[0]
                title = value

                variant_dict = {'title': title}
                item_data_list = []
                current_item = {}
                variant_data = []

                for item_key, item_value in self.request.data.items():
                    if f'variants[{index}][items]' in item_key:
                        field_name = item_key.split('[')[-1].split(']')[0]
                        if field_name == "title":
                            if current_item:
                                item_data_list.append(current_item)
                            current_item = {}
                        current_item.update({field_name: item_value})
                    
                if current_item:
                    item_data_list.append(current_item)

                variant_data.append({'variant_data': variant_dict, 'variant_item_data': item_data_list})

        for data_entry in variant_data:
            variant = api_models.Variant.objects.create(title=data_entry['variant_data']['title'], course=course_instance)

            for item_data in data_entry['variant_item_data']:
                preview_value = item_data.get("preview")
                preview = bool(strtobool(str(preview_value))) if preview_value is not None else False

                api_models.VariantItem.objects.create(
                    variant=variant,
                    title=item_data.get("title"),
                    description=item_data.get("description"),
                    file=item_data.get("file"),
                    preview=preview,
                )

    def save_nested_data(self, course_instance, serializer_class, data):
        serializer = serializer_class(data=data, many=True, context={"course_instance": course_instance})
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course_instance) 



class CourseUpdateAPIView(generics.RetrieveUpdateAPIView):
    querysect = api_models.Course.objects.all()
    serializer_class = api_serializer.CourseSerializer
    permisscion_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        course_id = self.kwargs['course_id']

        teacher = api_models.Teacher.objects.get(id=teacher_id)
        course = api_models.Course.objects.get(course_id=course_id)

        return course
    
    def update(self, request, *args, **kwargs):
        course = self.get_object()
        serializer = self.get_serializer(course, data=request.data)
        serializer.is_valid(raise_exception=True)

        if "image" in request.data and isinstance(request.data['image'], InMemoryUploadedFile):
            course.image = request.data['image']
        elif 'image' in request.data and str(request.data['image']) == "No File":
            course.image = None
        
        if 'file' in request.data and not str(request.data['file']).startswith("http://"):
            course.file = request.data['file']

        if 'category' in request.data['category'] and request.data['category'] != 'NaN' and request.data['category'] != "undefined":
            category = api_models.Category.objects.get(id=request.data['category'])
            course.category = category

        self.perform_update(serializer)
        self.update_variant(course, request.data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update_variant(self, course, request_data):
        for key, value in request_data.items():
            if key.startswith("variants") and '[variant_title]' in key:

                index = key.split('[')[1].split(']')[0]
                title = value

                id_key = f"variants[{index}][variant_id]"
                variant_id = request_data.get(id_key)

                variant_data = {'title': title}
                item_data_list = []
                current_item = {}

                for item_key, item_value in request_data.items():
                    if f'variants[{index}][items]' in item_key:
                        field_name = item_key.split('[')[-1].split(']')[0]
                        if field_name == "title":
                            if current_item:
                                item_data_list.append(current_item)
                            current_item = {}
                        current_item.update({field_name: item_value})
                    
                if current_item:
                    item_data_list.append(current_item)

                existing_variant = course.variant_set.filter(id=variant_id).first()

                if existing_variant:
                    existing_variant.title = title
                    existing_variant.save()

                    for item_data in item_data_list[1:]:
                        preview_value = item_data.get("preview")
                        preview = bool(strtobool(str(preview_value))) if preview_value is not None else False

                        variant_item = api_models.VariantItem.objects.filter(variant_item_id=item_data.get("variant_item_id")).first()

                        if not str(item_data.get("file")).startswith("http://"):
                            if item_data.get("file") != "null":
                                file = item_data.get("file")
                            else:
                                file = None
                            
                            title = item_data.get("title")
                            description = item_data.get("description")

                            if variant_item:
                                variant_item.title = title
                                variant_item.description = description
                                variant_item.file = file
                                variant_item.preview = preview
                            else:
                                variant_item = api_models.VariantItem.objects.create(
                                    variant=existing_variant,
                                    title=title,
                                    description=description,
                                    file=file,
                                    preview=preview
                                )
                        
                        else:
                            title = item_data.get("title")
                            description = item_data.get("description")

                            if variant_item:
                                variant_item.title = title
                                variant_item.description = description
                                variant_item.preview = preview
                            else:
                                variant_item = api_models.VariantItem.objects.create(
                                    variant=existing_variant,
                                    title=title,
                                    description=description,
                                    preview=preview
                                )
                        
                        variant_item.save()

                else:
                    new_variant = api_models.Variant.objects.create(
                        course=course, title=title
                    )

                    for item_data in item_data_list:
                        preview_value = item_data.get("preview")
                        preview = bool(strtobool(str(preview_value))) if preview_value is not None else False

                        api_models.VariantItem.objects.create(
                            variant=new_variant,
                            title=item_data.get("title"),
                            description=item_data.get("description"),
                            file=item_data.get("file"),
                            preview=preview,
                        )

    def save_nested_data(self, course_instance, serializer_class, data):
        serializer = serializer_class(data=data, many=True, context={"course_instance": course_instance})
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course_instance) 


class CourseDetailAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]
    
    def get_object(self):
        slug = self.kwargs['slug']
        if not slug:
            raise Http404("Course not found")
        return api_models.Course.objects.get(slug=slug)



    # def get_object(self):
    #     course_id = self.kwargs['course_id']
    #     return api_models.Course.objects.get(course_id=course_id)


class CourseVariantDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializer.VariantSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        variant_id = self.kwargs['variant_id']
        teacher_id = self.kwargs['teacher_id']
        course_id = self.kwargs['course_id']

        print("variant_id ========", variant_id)

        teacher = api_models.Teacher.objects.get(id=teacher_id)
        course = api_models.Course.objects.get(teacher=teacher, course_id=course_id)
        return api_models.Variant.objects.get(id=variant_id)
    
class CourseVariantItemDeleteAPIVIew(generics.DestroyAPIView):
    serializer_class = api_serializer.VariantItemSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        variant_id = self.kwargs['variant_id']
        variant_item_id = self.kwargs['variant_item_id']
        teacher_id = self.kwargs['teacher_id']
        course_id = self.kwargs['course_id']


        teacher = api_models.Teacher.objects.get(id=teacher_id)
        course = api_models.Course.objects.get(teacher=teacher, course_id=course_id)
        variant = api_models.Variant.objects.get(variant_id=variant_id, course=course)
        return api_models.VariantItem.objects.get(variant=variant, variant_item_id=variant_item_id)
    

class QuizListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = api_models.Quizzes.objects.all()
    serializer_class = api_serializer.QuizSerializer


# class QuestionListView(APIView):
#     def get(self, request, quiz_id):
#         questions = api_models.Question.objects.filter(quiz_id=quiz_id)
#         serializer = api_serializer.QuestionSerializer(questions, many=True)
#         return Response(serializer.data)


class RandomQuestionView(APIView):
    def get(self, request, quiz_id):
        import random
        questions = list(api_models.Question.objects.filter(quiz_id=quiz_id))
        if questions:
            question = random.choice(questions)
            serializer = api_serializer.QuestionSerializer(question)
            return Response(serializer.data)
        return Response({'error': 'No questions available'}, status=404)
    
class WritingQuestionListView(APIView):
    
    """
    Returns a list of writing questions for a specific quiz.
    """
    permission_classes = [AllowAny]
    def get(self, request, quiz_id):
        questions = api_models.Question.objects.filter(quiz_id=quiz_id, question_type='WRITING')
        serializer = api_serializer.QuestionSerializer(questions, many=True)
        return Response(serializer.data)


class RandomWritingQuestionView(APIView):
    """
    Returns a random writing question for a specific quiz.
    """
    def get(self, request, quiz_id):
        questions = list(api_models.Question.objects.filter(quiz_id=quiz_id, question_type='WRITING'))
        if questions:
            question = random.choice(questions)
            serializer = api_serializer.QuestionSerializer(question)
            return Response(serializer.data)
        return Response({'error': 'No writing questions available'}, status=404)


# class WritingAnswerCreateView(generics.CreateAPIView):
#     serializer_class = api_serializer.WritingAnswerSerializer

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)


class WritingAnswerFilteredListView(APIView):
    """
    Fetch all answers for a specific question filtered by user ID.
    """
    permission_classes = [AllowAny]

    def get(self, request, question_id, user_id):
        try:
            # Fetch the question
            question = api_models.Question.objects.get(id=question_id)

            # Filter answers by question and user
            writing_answers = api_models.WritingAnswer.objects.filter(question=question, user_id=user_id)

            # Serialize the writing answers
            serializer = api_serializer.WritingAnswerSerializer(writing_answers, many=True)
            return Response(serializer.data, status=200)
        except api_models.Question.DoesNotExist:
            return Response({'error': 'Question not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        
        
        
#Date 02/15/2025

# class TeacherListCreateView(APIView):
#     @swagger_auto_schema(
#         operation_description="List all teachers",
#         responses={200: api_serializer.CreateTeacherSerializer(many=True)}  # Specify response schema for GET
#     )
#     def get(self, request):
#         teachers = api_models.Teacher.objects.all()
#         serializer = api_serializer.CreateTeacherSerializer(teachers, many=True)
#         return Response(serializer.data)

#     @swagger_auto_schema(
#         request_body=api_serializer.CreateTeacherSerializer,  # Only for POST method
#         operation_description="Create a new teacher"
#     )
#     def post(self, request):
#         serializer = api_serializer.CreateTeacherSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeacherListCreateView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access
    """
    Handles GET requests to list all teachers and POST requests to create a new teacher.
    """

    @swagger_auto_schema(
        operation_description="List all teachers",
        responses={200: api_serializer.CreateTeacherSerializer(many=True)}  # Response schema for GET
    )
    def get(self, request):
        teachers = api_models.Teacher.objects.all()
        serializer = api_serializer.CreateTeacherSerializer(teachers, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=api_serializer.CreateTeacherSerializer,  # Request body for POST method
        operation_description="Create a new teacher"
    )
    def post(self, request):
        serializer = api_serializer.CreateTeacherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherDetailView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access
    """
    Handles GET, PUT, and DELETE requests for a specific teacher.
    """

    def get(self, request, teacher_id):
        try:
            teacher = api_models.Teacher.objects.get(id=teacher_id)
        except api_models.Teacher.DoesNotExist:
            raise NotFound("Teacher not found")
        
        serializer = api_serializer.CreateTeacherSerializer(teacher)
        return Response(serializer.data)

    def put(self, request, teacher_id):
        try:
            teacher = api_models.Teacher.objects.get(id=teacher_id)
        except api_models.Teacher.DoesNotExist:
            raise NotFound("Teacher not found")
        
        serializer = api_serializer.CreateTeacherSerializer(teacher, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, teacher_id):
        try:
            teacher = api_models.Teacher.objects.get(id=teacher_id)
        except api_models.Teacher.DoesNotExist:
            raise NotFound("Teacher not found")
        
        teacher.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserListView(generics.ListAPIView):
    # permission_classes = [AllowAny]  # Allow unauthenticated access
    queryset = User.objects.all()
    serializer_class = api_serializer.UserSerializer
    # permission_classes = [IsAuthenticated]
    
    
# Define the request body schema as OpenAPI components
group_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Group name')
    }
)

# quiz_request_schema = openapi.Schema(
#     type=openapi.TYPE_OBJECT,
#     properties={
#         'title': openapi.Schema(type=openapi.TYPE_STRING, description='Quiz title'),
#         'group': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
#             'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Group ID')
#         })
#     }
# )

quiz_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'title': openapi.Schema(type=openapi.TYPE_STRING, description='Quiz title'),
        'group': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Group ID')
            },
            required=['id']  # Ensure 'id' is required within 'group'
        ),
        'time_limit': openapi.Schema(type=openapi.TYPE_INTEGER, description='Time limit for the quiz in minutes')
    },
    required=['title', 'group', 'time_limit']  # Make all top-level fields required
)

question_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'title': openapi.Schema(type=openapi.TYPE_STRING, description='Question title'),
        'quiz': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quiz ID')
        }),
        'question_type': openapi.Schema(type=openapi.TYPE_STRING, description='Question type'),
        'answers': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
                'answer_text': openapi.Schema(type=openapi.TYPE_STRING, description='Answer text'),
                'is_right': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is the answer correct?')
            })
        )
    }
)


writing_answer_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'question': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Question ID')
            }
        ),
        'answer_text': openapi.Schema(type=openapi.TYPE_STRING, description='Written answer text'),
        # 'user' and 'submitted_at' are omitted since they’re set automatically
    },
    required=['question', 'answer_text']  # Only question and answer_text are required
)

# writing_answer_request_schema = openapi.Schema(
#     type=openapi.TYPE_OBJECT,
#     properties={
#         'question': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
#             'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Question ID')
#         }),
#         'user': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
#             'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID')
#         }),
#         'answer_text': openapi.Schema(type=openapi.TYPE_STRING, description='Written answer text'),
#         'submitted_at': openapi.Schema(type=openapi.TYPE_STRING, description='Timestamp of answer submission')
#     }
# )

# Group Views (POST and UPDATE)
class GroupCreateView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access
    @swagger_auto_schema(request_body=group_request_schema)
    def post(self, request, *args, **kwargs):
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GroupUpdateView(APIView):
    @swagger_auto_schema(request_body=group_request_schema)
    def put(self, request, *args, **kwargs):
        try:
            group = api_models.Group.objects.get(id=kwargs['pk'])
        except api_models.Group.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = GroupSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GroupListView(APIView):
    def get(self, request, *args, **kwargs):
        groups = api_models.Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GroupDetailView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            group = api_models.Group.objects.get(id=kwargs['pk'])
        except api_models.Group.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = GroupSerializer(group)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GroupDeleteView(APIView):
    def delete(self, request, *args, **kwargs):
        try:
            group = api_models.Group.objects.get(id=kwargs['pk'])
        except api_models.Group.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Quiz Views (POST and UPDATE)
class QuizCreateView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access
    @swagger_auto_schema(request_body=quiz_request_schema)
    def post(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = QuizSerializer(data=request.data, many=True)
        else:
            serializer = QuizSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuizUpdateView(APIView):
    @swagger_auto_schema(request_body=quiz_request_schema)
    def put(self, request, *args, **kwargs):
        try:
            quiz = api_models.Quizzes.objects.get(id=kwargs['pk'])
        except api_models.Quizzes.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = QuizSerializer(quiz, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Question Views (POST and UPDATE)
class QuestionCreateView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access
    @swagger_auto_schema(request_body=question_request_schema)
    def post(self, request, *args, **kwargs):
        # Check if the input data is a list
        if isinstance(request.data, list):
            serializer = QuestionSerializer(data=request.data, many=True)
        else:
            serializer = QuestionSerializer(data=request.data)
            
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuestionUpdateView(APIView):
    @swagger_auto_schema(
        request_body=question_request_schema,
        responses={
            200: "Question(s) updated successfully",
            404: "Question not found",
            400: "Invalid request data",
            500: "Internal server error"
        }
    )
    def put(self, request, *args, **kwargs):
        try:
            # Check if the input data is a list (bulk update) or a single dictionary
            is_list = isinstance(request.data, list)
            data = request.data if is_list else [request.data]  # Wrap single dict in a list
            
            # If URL includes a specific pk, ensure we're updating that question only
            pk = kwargs.get('pk')
            if pk and is_list:
                return Response(
                    {"detail": "Bulk update not allowed when specifying a single question ID."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            updated_questions = []
            errors = []

            for item in data:
                if pk:  # Single question update via URL pk
                    try:
                        question = api_models.Question.objects.get(id=pk)
                    except api_models.Question.DoesNotExist:
                        return Response(
                            {"detail": f"Question with id {pk} not found."},
                            status=status.HTTP_404_NOT_FOUND
                        )
                else:  # Bulk update expects 'id' in each item
                    question_id = item.get('id')
                    if not question_id:
                        errors.append({"item": item, "error": "Question ID is required for bulk update."})
                        continue
                    try:
                        question = api_models.Question.objects.get(id=question_id)
                    except api_models.Question.DoesNotExist:
                        errors.append({"item": item, "error": f"Question with id {question_id} not found."})
                        continue

                serializer = QuestionSerializer(question, data=item, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    updated_questions.append(serializer.data)
                else:
                    errors.append({"item": item, "errors": serializer.errors})

            if errors:
                return Response(
                    {"updated": updated_questions, "errors": errors},
                    status=status.HTTP_400_BAD_REQUEST if not updated_questions else status.HTTP_207_MULTI_STATUS
                )
            return Response(
                updated_questions if is_list else updated_questions[0],
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to update question(s): {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
# class QuestionUpdateView(APIView):
#     @swagger_auto_schema(request_body=question_request_schema)
#     def put(self, request, *args, **kwargs):
#         try:
#             question = api_models.Question.objects.get(id=kwargs['pk'])
#         except api_models.Question.DoesNotExist:
#             return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

#         serializer = QuestionSerializer(question, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# class QuestionListView(APIView):
#     def get(self, request, *args, **kwargs):
#         questions = api_models.Question.objects.all()
#         serializer = QuestionSerializer(questions, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

# class QuestionDetailView(APIView):
#     def get(self, request, *args, **kwargs):
#         try:
#             question = api_models.Question.objects.get(id=kwargs['pk'])
#         except api_models.Question.DoesNotExist:
#             return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
#         serializer = QuestionSerializer(question)
#         return Response(serializer.data, status=status.HTTP_200_OK)

class QuestionListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        questions = api_models.Question.objects.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# View using the new serializer
# Updated View
class QuestionByQuizView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, quiz_id, *args, **kwargs):
        try:
            quiz_id = int(quiz_id)  # Ensure quiz_id is an integer
            if not api_models.Quizzes.objects.filter(id=quiz_id).exists():
                return Response(
                    {"detail": "Quiz with this ID does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            questions = api_models.Question.objects.filter(quiz_id=quiz_id)
            if not questions.exists():
                return Response(
                    {"detail": "No questions found for the given quiz_id."},
                    status=status.HTTP_404_NOT_FOUND
                )
        except ValueError:
            return Response(
                {"detail": "Invalid quiz_id provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = api_serializer.SimpleQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class QuestionDetailView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        try:
            question = api_models.Question.objects.get(id=kwargs['pk'])
        except api_models.Question.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = QuestionSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)

class QuestionDeleteView(APIView):
    def delete(self, request, *args, **kwargs):
        try:
            question = api_models.Question.objects.get(id=kwargs['pk'])
        except api_models.Question.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WritingAnswerListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        writing_answers = api_models.WritingAnswer.objects.all()
        serializer = WritingAnswerSerializer(writing_answers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Writing Answer Views (POST and UPDATE)
# class WritingAnswerCreateView(APIView):
#     @swagger_auto_schema(request_body=writing_answer_request_schema)
#     def post(self, request, *args, **kwargs):
#         serializer = WritingAnswerSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class WritingAnswerCreateView(APIView):
#     permission_classes = [IsAuthenticated]  # Ensure user is 
#     # permission_classes = [AllowAny]


#     @swagger_auto_schema(request_body=writing_answer_request_schema)
#     def post(self, request, *args, **kwargs):
#         serializer = WritingAnswerSerializer(
#             data=request.data,
#             context={'request': request}  # Pass request to serializer context
#         )
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


writing_answer_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'question': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Question ID')
            },
            required=['id']
        ),
        'answer_text': openapi.Schema(type=openapi.TYPE_STRING, description='Written answer text'),
    },
    required=['question', 'answer_text']
)

class WritingAnswerCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=writing_answer_request_schema)
    def post(self, request, *args, **kwargs):
        serializer = WritingAnswerSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            # Save the WritingAnswer
            writing_answer = serializer.save()
            
            # Automatically create a WritingAnswerReview with status 'ANSWERED'
            api_models.WritingAnswerReview.objects.create(
                writing_answer=writing_answer,
                availability_status='ANSWERED'
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# writing_answer_request_schema = openapi.Schema(
#     type=openapi.TYPE_OBJECT,
#     properties={
#         'question': openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             properties={
#                 'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Question ID')
#             },
#             required=['id']
#         ),
#         'answer_text': openapi.Schema(type=openapi.TYPE_STRING, description='Written answer text'),
#     },
#     required=['question', 'answer_text']
# )

# class WritingAnswerCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(request_body=writing_answer_request_schema)
#     def post(self, request, *args, **kwargs):
#         serializer = WritingAnswerSerializer(
#             data=request.data,
#             context={'request': request}
#         )
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class WritingAnswerUpdateView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated
    # permission_classes = [AllowAny]


    @swagger_auto_schema(request_body=writing_answer_request_schema)
    def put(self, request, *args, **kwargs):
        try:
            writing_answer = api_models.WritingAnswer.objects.get(id=kwargs['pk'])
        except api_models.WritingAnswer.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = WritingAnswerSerializer(
            writing_answer,
            data=request.data,
            partial=True,
            context={'request': request}  # Pass request to serializer context
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# class WritingAnswerUpdateView(APIView):
#     @swagger_auto_schema(request_body=writing_answer_request_schema)
#     def put(self, request, *args, **kwargs):
#         try:
#             writing_answer = api_models.WritingAnswer.objects.get(id=kwargs['pk'])
#         except api_models.WritingAnswer.DoesNotExist:
#             return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

#         serializer = WritingAnswerSerializer(writing_answer, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



class WritingAnswerDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            writing_answer = api_models.WritingAnswer.objects.get(id=kwargs['pk'])
        except api_models.WritingAnswer.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = WritingAnswerSerializer(writing_answer)
        return Response(serializer.data, status=status.HTTP_200_OK)

class WritingAnswerDeleteView(APIView):
    def delete(self, request, *args, **kwargs):
        try:
            writing_answer = api_models.WritingAnswer.objects.get(id=kwargs['pk'])
        except api_models.WritingAnswer.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        writing_answer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class WritingAnswersByUserView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="ID of the user to fetch writing answers for",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: WritingAnswerSerializer(many=True),
            404: "User not found or no answers available"
        }
    )
    def get(self, request, user_id, *args, **kwargs):
        try:
            # Check if the user exists (optional)
            user = api_models.User.objects.get(id=user_id)
        except api_models.User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch all writing answers for the user
        writing_answers = api_models.WritingAnswer.objects.filter(user=user)
        if not writing_answers.exists():
            return Response({"detail": "No writing answers found for this user."}, status=status.HTTP_404_NOT_FOUND)

        serializer = WritingAnswerSerializer(writing_answers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# class MCQAnswerCreateView(APIView):
#     @swagger_auto_schema(request_body=api_serializer.MCQAnswerSerializer(many=True))
#     def post(self, request, *args, **kwargs):
#         serializer = api_serializer.MCQAnswerSerializer(data=request.data, many=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MCQAnswerCreateView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    @swagger_auto_schema(request_body=api_serializer.MCQAnswerSerializer(many=True))
    def post(self, request, *args, **kwargs):
        serializer = api_serializer.MCQAnswerSerializer(
            data=request.data, 
            many=True, 
            context={'request': request}  # Pass request to serializer context
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MCQAnswerUpdateView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    @swagger_auto_schema(request_body=api_serializer.MCQAnswerSerializer)
    def put(self, request, *args, **kwargs):
        try:
            mcq_answer = api_models.MCQAnswer.objects.get(id=kwargs['pk'])
        except api_models.MCQAnswer.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = api_serializer.MCQAnswerSerializer(
            mcq_answer, 
            data=request.data, 
            partial=True, 
            context={'request': request}  # Pass request to serializer context
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class MCQAnswerUpdateView(APIView):
#     @swagger_auto_schema(request_body=api_serializer.MCQAnswerSerializer)
#     def put(self, request, *args, **kwargs):
#         try:
#             mcq_answer = api_models.MCQAnswer.objects.get(id=kwargs['pk'])
#         except api_models.MCQAnswer.DoesNotExist:
#             return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

#         serializer = api_serializer.MCQAnswerSerializer(mcq_answer, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MCQAnswerListView(APIView):
    def get(self, request, *args, **kwargs):
        mcq_answers = api_models.MCQAnswer.objects.all()
        serializer = api_serializer.MCQAnswerSerializer(mcq_answers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MCQAnswerDetailView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            mcq_answer = api_models.MCQAnswer.objects.get(id=kwargs['pk'])
        except api_models.MCQAnswer.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = api_serializer.MCQAnswerSerializer(mcq_answer)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MCQAnswerDeleteView(APIView):
    def delete(self, request, *args, **kwargs):
        try:
            mcq_answer = api_models.MCQAnswer.objects.get(id=kwargs['pk'])
        except api_models.MCQAnswer.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        mcq_answer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class StandardPagination(PageNumberPagination):
    page_size = 10  # Default number of items per page
    page_size_query_param = 'page_size'  # Allow client to override page size
    max_page_size = 100  # Maximum allowed page size
    

class MCQAnswersByUserView(APIView):
    permission_classes = [IsAuthenticated]  # Require authentication
    pagination_class = StandardPagination  # Use custom pagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="ID of the user to fetch MCQ answers for",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Number of items per page",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: api_serializer.MCQAnswerSerializer(many=True),
            403: "You can only view your own answers",
            404: "User not found or no answers available"
        }
    )
    def get(self, request, user_id, *args, **kwargs):
        # Check if the authenticated user matches the requested user_id
        if request.user.id != user_id:
            return Response(
                {"detail": "You can only view your own answers."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Check if the user exists
            user = api_models.User.objects.get(id=user_id)
        except api_models.User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch all MCQ answers for the user
        mcq_answers = api_models.MCQAnswer.objects.filter(user=user)
        if not mcq_answers.exists():
            return Response({"detail": "No MCQ answers found for this user."}, status=status.HTTP_404_NOT_FOUND)

        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(mcq_answers, request)
        serializer = api_serializer.MCQAnswerSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class WritingAnswersByUserView(APIView):
    permission_classes = [IsAuthenticated]  # Require authentication
    pagination_class = StandardPagination  # Use custom pagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="ID of the user to fetch writing answers for",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Number of items per page",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: WritingAnswerSerializer(many=True),
            403: "You can only view your own answers",
            404: "User not found or no answers available"
        }
    )
    def get(self, request, user_id, *args, **kwargs):
        # Check if the authenticated user matches the requested user_id
        if request.user.id != user_id:
            return Response(
                {"detail": "You can only view your own answers."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Check if the user exists
            user = api_models.User.objects.get(id=user_id)
        except api_models.User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch all writing answers for the user
        writing_answers = api_models.WritingAnswer.objects.filter(user=user)
        if not writing_answers.exists():
            return Response({"detail": "No writing answers found for this user."}, status=status.HTTP_404_NOT_FOUND)

        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(writing_answers, request)
        serializer = WritingAnswerSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
class NonAuthenTicateMCQAnswersByUserView(APIView):
    pagination_class = StandardPagination  # Use custom pagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="ID of the user to fetch MCQ answers for",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Number of items per page",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: api_serializer.MCQAnswerSerializer(many=True),
            404: "User not found or no answers available"
        }
    )
    def get(self, request, user_id, *args, **kwargs):
        try:
            # Check if the user exists
            user = api_models.User.objects.get(id=user_id)
        except api_models.User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch all MCQ answers for the user
        mcq_answers = api_models.MCQAnswer.objects.filter(user=user)
        if not mcq_answers.exists():
            return Response({"detail": "No MCQ answers found for this user."}, status=status.HTTP_404_NOT_FOUND)

        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(mcq_answers, request)
        serializer = api_serializer.MCQAnswerSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class NonAuthenTicateWritingAnswersByUserView(APIView):
    permission_classes = [AllowAny]

    pagination_class = StandardPagination  # Use custom pagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="ID of the user to fetch writing answers for",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Number of items per page",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: WritingAnswerSerializer(many=True),
            404: "User not found or no answers available"
        }
    )
    def get(self, request, user_id, *args, **kwargs):
        try:
            # Check if the user exists
            user = api_models.User.objects.get(id=user_id)
        except api_models.User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch all writing answers for the user
        writing_answers = api_models.WritingAnswer.objects.filter(user=user)
        if not writing_answers.exists():
            return Response({"detail": "No writing answers found for this user."}, status=status.HTTP_404_NOT_FOUND)

        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(writing_answers, request)
        serializer = WritingAnswerSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class AnswerCountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        question_id = kwargs.get('question_id')
        try:
            question = api_models.Question.objects.get(id=question_id)
        except api_models.Question.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        mcq_correct_count = question.mcq_answers.filter(selected_answer__is_right=True).count()
        total_mcq_answers = question.mcq_answers.count()
        total_writing_answers = question.writing_answers.count()

        return Response({
            "total_mcq_answers": total_mcq_answers,
            "mcq_correct_count": mcq_correct_count,
            "total_writing_answers": total_writing_answers
        }, status=status.HTTP_200_OK)


# Create a new Category
class CategoryCreateView(generics.CreateAPIView):
    queryset = api_models.Category.objects.all()
    serializer_class = api_serializer.CategorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# Retrieve, Update, and Delete a Category
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = api_models.Category.objects.all()
    serializer_class = api_serializer.CategorySerializer
    lookup_field = 'slug'  # Use slug instead of pk for lookups

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)  # Support PATCH (partial updates)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    


# Custom permission class (unchanged)
# class IsAdminUser(permissions.BasePermission):
#     def has_permission(self, request, view):
#         return bool(request.user and request.user.can_login_as_admin())

# class AdminView(APIView):
#     serializer_class = api_serializer.AdminSerializer

#     def post(self, request):
#         # Validate request data
#         login_serializer = api_serializer.AdminLoginSerializer(data=request.data)
#         if not login_serializer.is_valid():
#             return Response({
#                 "error": login_serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # Get email and password from request
#         email = login_serializer.validated_data['email']
#         password = login_serializer.validated_data['password']

#         # Authenticate user
#         user = authenticate(request=request, email=email, password=password)
        
#         if user is None:
#             return Response({
#                 "error": "Invalid email or password"
#             }, status=status.HTTP_401_UNAUTHORIZED)

#         # Check if user can login as admin
#         if not user.can_login_as_admin():
#             return Response({
#                 "error": "User is not authorized as admin"
#             }, status=status.HTTP_403_FORBIDDEN)

#         # Generate tokens using Simple JWT
#         refresh = RefreshToken.for_user(user)
#         access_token = str(refresh.access_token)

#         # Serialize user data
#         serializer = self.serializer_class(user)
#         return Response({
#             "message": "Welcome Admin",
#             "user": serializer.data,
#             "access_token": access_token,
#             "refresh_token": str(refresh)
#         }, status=status.HTTP_200_OK)


class GroupQuizDetailsView(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'group_id',
                openapi.IN_PATH,
                description="ID of the group to fetch",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: api_serializer.GroupDetailSerializer,  # Updated serializer
            404: "Group not found"
        }
    )
    def get(self, request, group_id, *args, **kwargs):
        try:
            group = api_models.Group.objects.prefetch_related(
                'quizzes__questions__answers'
            ).get(id=group_id)
        except api_models.Group.DoesNotExist:
            return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = api_serializer.GroupDetailSerializer(group)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class GroupQuizByQuestionTypeView(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'group_id',
                openapi.IN_PATH,
                description="ID of the group to fetch",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'question_type',
                openapi.IN_QUERY,
                description="Type of questions to filter (e.g., 'MCQ' or 'WRITING')",
                type=openapi.TYPE_STRING,
                enum=['MCQ', 'WRITING'],
                required=True
            )
        ],
        responses={
            200: api_serializer.GroupDetailSerializer,
            404: "Group not found",
            400: "Invalid question type"
        }
    )
    def get(self, request, group_id, *args, **kwargs):
        # Get the question_type from query parameters
        question_type = request.query_params.get('question_type', None)
        
        # Validate question_type
        valid_question_types = [choice[0] for choice in api_models.Question.QUIZ_TYPES]
        if not question_type or question_type not in valid_question_types:
            return Response(
                {"detail": f"Invalid question type. Must be one of: {', '.join(valid_question_types)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the group with related data
        try:
            group = api_models.Group.objects.prefetch_related(
                'quizzes__questions__answers'
            ).get(id=group_id)
        except api_models.Group.DoesNotExist:
            return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get serialized data
        serializer = api_serializer.GroupDetailSerializer(group)
        data = serializer.data

        # Filter questions by question_type
        for quiz in data['quizzes']:
            quiz['questions'] = [
                q for q in quiz['questions'] if q['question_type'] == question_type
            ]

        # Remove quizzes with no matching questions (optional)
        data['quizzes'] = [quiz for quiz in data['quizzes'] if quiz['questions']]

        return Response(data, status=status.HTTP_200_OK)
    

# class WritingAnswerReviewListView(APIView):
#     # permission_classes = [IsAdminUser]
#     permission_classes = [AllowAny]
    
#     def get(self, request, *args, **kwargs):
#         reviews = api_models.WritingAnswerReview.objects.all()
#         serializer = api_serializer.WritingAnswerReviewSerializer(reviews, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
  
class WritingAnswerReviewListView(APIView):
    # permission_classes = [IsAdminUser]
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        reviews = api_models.WritingAnswerReview.objects.all()
        serializer = api_serializer.WritingAnswerReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)  

# Define the request schema
writing_answer_review_update_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'availability_status': openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=['CREATED', 'ANSWERED', 'CHECKED'],
            description='Status of the writing answer review',
            default='CREATED'
        ),
        'remarks': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Teacher remarks on the answer (required if status is CHECKED)',
            nullable=True
        ),
        'checked_at': openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description='Timestamp when the answer was checked (required if status is CHECKED)',
            nullable=True,
            example='2025-03-29T15:00:00Z'
        ),
        'teacher': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='ID of the teacher reviewing the answer',
            nullable=True
        ),
    },
    required=[]  # No fields are strictly required for PATCH (partial update)
)

# Define the response schema (reusing the full response structure)
writing_answer_review_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_STRING, description='Unique ID of the review'),
        'question': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'question_id': openapi.Schema(type=openapi.TYPE_STRING),
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'question_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['MCQ', 'WRITING']),
                'quiz_id': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        'user': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                'username': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        'answer_details': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'answer_text': openapi.Schema(type=openapi.TYPE_STRING),
                'submitted_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'availability_status': openapi.Schema(type=openapi.TYPE_STRING, enum=['CREATED', 'ANSWERED', 'CHECKED']),
                'question_answers': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_STRING),
                            'answer_text': openapi.Schema(type=openapi.TYPE_STRING),
                            'is_right': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        }
                    )
                ),
            }
        ),
        'teacher_review': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'remarks': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'checked_by': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'checked_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, nullable=True),
            }
        ),
        'date_updated': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
    }
)

# Update View with Schema
class WritingAnswerReviewUpdateView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=writing_answer_review_update_schema,
        responses={
            200: writing_answer_review_response_schema,
            400: openapi.Response('Bad Request', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            404: openapi.Response('Not Found', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
            ))
        },
        operation_description="Update a WritingAnswerReview instance partially."
    )
    def patch(self, request, review_id, *args, **kwargs):
        try:
            review = api_models.WritingAnswerReview.objects.get(id=review_id)
        except api_models.WritingAnswerReview.DoesNotExist:
            return Response(
                {"error": "WritingAnswerReview not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = api_serializer.WritingAnswerReviewUpdateSerializer(
            review, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            updated_serializer = api_serializer.WritingAnswerReviewSerializer(review)
            return Response(updated_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class VariantListView(ListAPIView):
    queryset = api_models.Variant.objects.all()
    serializer_class = api_serializer.VariantSerializer
    permission_classes = [AllowAny]  # Adjust as needed

    def get_serializer_context(self):
        """
        Pass request context to serializer to handle depth logic.
        """
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class VariantDetailView(RetrieveAPIView):
    queryset = api_models.Variant.objects.all()
    serializer_class = api_serializer.VariantSerializer
    permission_classes = [AllowAny]  # Adjust as needed

    def get_serializer_context(self):
        """
        Pass request context to serializer to handle depth logic.
        """
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class VariantItemListView(ListAPIView):
    queryset = api_models.VariantItem.objects.all()
    serializer_class = api_serializer.VariantItemSerializer
    permission_classes = [AllowAny]  # Adjust as needed

    def get_queryset(self):
        """
        Optional: Filter by variant_id if provided in query params.
        """
        queryset = api_models.VariantItem.objects.all()
        variant_id = self.request.query_params.get('variant_id', None)
        if variant_id is not None:
            queryset = queryset.filter(variant_id=variant_id)
        return queryset

    def get_serializer_context(self):
        """
        Pass request context to serializer to handle depth logic.
        """
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class VariantItemDetailView(RetrieveAPIView):
    queryset = api_models.VariantItem.objects.all()
    serializer_class = api_serializer.VariantItemSerializer
    # permission_classes = [IsAuthenticated]  # Adjust as needed
    permission_classes = [AllowAny]  # Adjust as needed

    def get_serializer_context(self):
        """
        Pass request context to serializer to handle depth logic.
        """
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    

class WritingAnswerReviewByUserAPIView(APIView):
    permission_classes = [AllowAny]

    # Define the response schema (reusing existing schema structure)
    response_schema = openapi.Schema(
        type=openapi.TYPE_ARRAY,
        items=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, description='Unique ID of the review'),
                'question': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'question_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                        'question_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['MCQ', 'WRITING']),
                        'quiz_id': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
                'user': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
                'answer_details': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'answer_text': openapi.Schema(type=openapi.TYPE_STRING),
                        'submitted_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'availability_status': openapi.Schema(type=openapi.TYPE_STRING, enum=['CREATED', 'ANSWERED', 'CHECKED']),
                        'question_answers': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'answer_text': openapi.Schema(type=openapi.TYPE_STRING),
                                    'is_right': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                }
                            )
                        ),
                    }
                ),
                'teacher_review': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'remarks': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'checked_by': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'checked_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, nullable=True),
                    }
                ),
                'date_updated': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            }
        )
    )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description='ID of the user to filter writing answer reviews',
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: response_schema,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        }
    )
    def get(self, request, user_id, *args, **kwargs):
        try:
            reviews = api_models.WritingAnswerReview.objects.filter(writing_answer__user__id=user_id)
            if not reviews.exists():
                return Response(
                    {'detail': f'No writing answer reviews found for user_id {user_id}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = api_serializer.WritingAnswerReviewSerializer(reviews, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {'detail': 'Invalid user_id format'},
                status=status.HTTP_400_BAD_REQUEST
            )