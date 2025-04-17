from api import views as api_views
from django.urls import path
from api import admin

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Authentication Endpoints

    path("user/token/", api_views.MyTokenObtainPairView.as_view()),
    path('admin/login/', api_views.AdminView.as_view(), name='admin-login'),
    path("user/token/refresh/", TokenRefreshView.as_view()),
    path("user/register/", api_views.RegisterView.as_view()),
    path("user/password-reset/<email>/", api_views.PasswordResetEmailVerifyAPIView.as_view()),
    path("user/password-change/", api_views.PasswordChangeAPIView.as_view()),
    path("user/profile/<user_id>/", api_views.ProfileAPIView.as_view()),
    path("user/change-password/", api_views.ChangePasswordAPIView.as_view()),
    path('user/users-list/', api_views.UserListView.as_view(), name='user-list'),

    # Core Endpoints
    path("course/category/", api_views.CategoryListAPIView.as_view()),
    path("course/course-list/", api_views.CourseListAPIView.as_view()),
    path("course/categories/create/", api_views.CategoryCreateView.as_view(), name='category-create'),
    
    # Retrieve, update, or delete a category by slug
    path("course/categories/<slug:slug>/", api_views.CategoryDetailView.as_view(), name='category-detail'),
    
    path("course/search/", api_views.SearchCourseAPIView.as_view()),
    # path("course/course-detail/<slug>/", api_views.CourseDetailAPIView.as_view()),
    path('course-detail/<slug:slug>/', api_views.CourseDetailAPIView.as_view(), name='course-detail'), ##Change this url 1-25-25
    path("course/cart/", api_views.CartAPIView.as_view()),
    path("course/cart-list/<cart_id>/", api_views.CartListAPIView.as_view()),
    path("course/cart-list/user/<user_id>/", api_views.CartListByUserAPIView.as_view()),
    path("course/cart-list/update/user/<int:user_id>/", api_views.CartUpdateByUserAPIView.as_view(), name="cart_update_by_user_id"),
    path("course/cart/update/<cart_id>/user/<int:user_id>/", api_views.CartUpdateByCartAndUserAPIView.as_view(), name="cart_update_by_cart_and_user_id"),
    path("cart/stats/<cart_id>/", api_views.CartStatsAPIView.as_view()),
    path("cart/stats/user/<int:user_id>/", api_views.CartStatsByUserAPIView.as_view(), name="cart_stats_by_user_id"),
    path("course/cart-item-delete/<cart_id>/<item_id>/", api_views.CartItemDeleteAPIView.as_view()),
    path("order/create-order/", api_views.CreateOrderAPIView.as_view()),
    path("order/checkout/<oid>/", api_views.CheckoutAPIView.as_view()),
    path("order/coupon/", api_views.CouponApplyAPIView.as_view()),
    path("payment/stripe-checkout/<order_oid>/", api_views.StripeCheckoutAPIView.as_view()),
    path("payment/payment-sucess/", api_views.PaymentSuccessAPIView.as_view()),


    # Student API Endpoints
    path("student/summary/<user_id>/", api_views.StudentSummaryAPIView.as_view()),
    path("student/course-list/<user_id>/", api_views.StudentCourseListAPIView.as_view()),
    path("student/course-detail/<user_id>/<enrollment_id>/", api_views.StudentCourseDetailAPIView.as_view()),
    path("student/course-completed/", api_views.StudentCourseCompletedCreateAPIView.as_view()),
    path("student/course-note/<user_id>/<enrollment_id>/", api_views.StudentNoteCreateAPIView.as_view()),
    path("student/course-note-detail/<user_id>/<enrollment_id>/<note_id>/", api_views.StudentNoteDetailAPIView.as_view()),
    path("student/rate-course/", api_views.StudentRateCourseCreateAPIView.as_view()),
    path("student/review-detail/<user_id>/<review_id>/", api_views.StudentRateCourseUpdateAPIView.as_view()),
    path("student/wishlist/<user_id>/", api_views.StudentWishListListCreateAPIView.as_view()),
    path("student/question-answer-list-create/<course_id>/", api_views.QuestionAnswerListCreateAPIView.as_view()),
    path("student/question-answer-message-create/", api_views.QuestionAnswerMessageSendAPIView.as_view()),
    
    path('course/variants/', api_views.VariantListView.as_view(), name='variant-list'),
    path('course/variants/<int:pk>/', api_views.VariantDetailView.as_view(), name='variant-detail'),
    path('course/variant-items/', api_views.VariantItemListView.as_view(), name='variant-item-list'),
    path('course/variant-items/<int:pk>/', api_views.VariantItemDetailView.as_view(), name='variant-item-detail'),


    # Teacher Routes
    # Teacher list and creation
    path('teacher/', api_views.TeacherListCreateView.as_view(), name='teacher-list-create'),

    # Teacher detail (GET, PUT, DELETE)
    path('teacher/<int:teacher_id>/', api_views.TeacherDetailView.as_view(), name='teacher-detail'),
    
    path("teacher/summary/<teacher_id>/", api_views.TeacherSummaryAPIView.as_view()),
    path("teacher/course-lists/<teacher_id>/", api_views.TeacherCourseListAPIView.as_view()),
    path("teacher/review-lists/<teacher_id>/", api_views.TeacherReviewListAPIView.as_view()),
    path("teacher/review-detail/<teacher_id>/<review_id>/", api_views.TeacherReviewDetailAPIView.as_view()),
    path("teacher/student-lists/<teacher_id>/", api_views.TeacherStudentsListAPIVIew.as_view({'get': 'list'})),
    path("teacher/all-months-earning/<teacher_id>/", api_views.TeacherAllMonthEarningAPIView),
    path("teacher/best-course-earning/<teacher_id>/", api_views.TeacherBestSellingCourseAPIView.as_view({'get': 'list'})),
    path("teacher/course-order-list/<teacher_id>/", api_views.TeacherCourseOrdersListAPIView.as_view()),
    path("teacher/question-answer-list/<teacher_id>/", api_views.TeacherQuestionAnswerListAPIView.as_view()),
    path("teacher/coupon-list/<teacher_id>/", api_views.TeacherCouponListCreateAPIView.as_view()),
    path("teacher/coupon-detail/<teacher_id>/<coupon_id>/", api_views.TeacherCouponDetailAPIView.as_view()),
    path("teacher/noti-list/<teacher_id>/", api_views.TeacherNotificationListAPIView.as_view()),
    path("teacher/noti-detail/<teacher_id>/<noti_id>", api_views.TeacherNotificationDetailAPIView.as_view()),
    path("teacher/course-create/", api_views.CourseCreateAPIView.as_view()),
    path("teacher/course-update/<teacher_id>/<course_id>/", api_views.CourseUpdateAPIView.as_view()),
    # path("teacher/course-detail/<course_id>/", api_views.CourseDetailAPIView.as_view()),
    path("teacher/course-detail/<slug:slug>/", api_views.CourseDetailAPIView.as_view()),
    path("teacher/course/variant-delete/<variant_id>/<teacher_id>/<course_id>/", api_views.CourseVariantDeleteAPIView.as_view()),
    path("teacher/course/variant-item-delete/<variant_id>/<variant_item_id>/<teacher_id>/<course_id>/", api_views.CourseVariantItemDeleteAPIVIew.as_view()),
    
    
    path('quizzes/', api_views.QuizListView.as_view(), name='quiz-list'),
    path('quizzes/<int:quiz_id>/questions/', api_views.QuestionListView.as_view(), name='question-list'),
    
    path('quizzes/<int:quiz_id>/random-question/', api_views.RandomQuestionView.as_view(), name='random-question'),
    
    path('quizzes/<int:quiz_id>/writing-questions/', api_views.WritingQuestionListView.as_view(), name='writing-question-list'),
    path('quizzes/<int:quiz_id>/random-writing-question/', api_views.RandomWritingQuestionView.as_view(), name='random-writing-question'),
    # path('writing-answers/', api_views.WritingAnswerCreateView.as_view(), name='writing-answer-create'),
    path('writing-answers/<int:question_id>/user/<int:user_id>/', api_views.WritingAnswerFilteredListView.as_view(), name='writing-answer-filtered-list'),
    
    # Group URLs
    path('groups/', api_views.GroupListView.as_view(), name='group-list'),
    path('groups/create/', api_views.GroupCreateView.as_view(), name='group-create'),
    path('groups/<int:pk>/', api_views.GroupDetailView.as_view(), name='group-detail'),
    path('groups/<int:pk>/update/', api_views.GroupUpdateView.as_view(), name='group-update'),
    path('groups/<int:pk>/delete/', api_views.GroupDeleteView.as_view(), name='group-delete'),
    path('groups/<int:group_id>/details/', api_views.GroupQuizDetailsView.as_view(), name='group-quiz-details'),
    path('groups/<int:group_id>/quiz-by-type/', api_views.GroupQuizByQuestionTypeView.as_view(), name='group-quiz-by-type'),

    # Quiz URLs
    path('quizzes/create/', api_views.QuizCreateView.as_view(), name='quiz-create'),
    path('quizzes/<int:pk>/', api_views.QuizUpdateView.as_view(), name='quiz-update'),

    # Question URLs
    path('questions/', api_views.QuestionListView.as_view(), name='question-list'),
    path('questions/create/', api_views.QuestionCreateView.as_view(), name='question-create'),
    path('questions/<int:pk>/', api_views.QuestionDetailView.as_view(), name='question-detail'),
    path('questions/<int:pk>/update/', api_views.QuestionUpdateView.as_view(), name='question-update'),
    path('questions/<int:pk>/delete/', api_views.QuestionDeleteView.as_view(), name='question-delete'),
    path('admin/writing-answer-reviews/', api_views.WritingAnswerReviewListView.as_view(), name='writing_answer_review_list'),
    path('admin/writing-answer-reviews/<str:review_id>/update/', api_views.WritingAnswerReviewUpdateView.as_view(), name='writing_answer_review_update'),
    path('admin/writing-answer-reviews-user/<str:user_id>/', api_views.WritingAnswerReviewByUserAPIView.as_view(), name='writing_answer_review_user'),

    # Writing Answer URLs
    path('writing-answers/', api_views.WritingAnswerListView.as_view(), name='writing-answer-list'),
    path('writing-answers/create/', api_views.WritingAnswerCreateView.as_view(), name='writing-answer-create'),
    path('writing-answers/<int:pk>/', api_views.WritingAnswerDetailView.as_view(), name='writing-answer-detail'),
    path('writing-answers/<int:pk>/update/', api_views.WritingAnswerUpdateView.as_view(), name='writing-answer-update'),
    path('writing-answers/<int:pk>/delete/', api_views.WritingAnswerDeleteView.as_view(), name='writing-answer-delete'),
    path('writing-answers/<int:user_id>/', api_views.WritingAnswersByUserView.as_view(), name='writing-answers-by-user'),
    path('writing-answers/non_authen/<int:user_id>/', api_views.NonAuthenTicateWritingAnswersByUserView.as_view(), name='writing-answers-by-non-athun-ser'),

    
    path('mcq-answers/', api_views.MCQAnswerListView.as_view(), name='mcq-answer-list'),
    path('mcq-answers/create/', api_views.MCQAnswerCreateView.as_view(), name='mcq-answer-create'),
    path('mcq-answers/<int:pk>/', api_views.MCQAnswerDetailView.as_view(), name='mcq-answer-detail'),
    path('mcq-answers/<int:pk>/update/', api_views.MCQAnswerUpdateView.as_view(), name='mcq-answer-update'),
    path('mcq-answers/<int:pk>/delete/', api_views.MCQAnswerDeleteView.as_view(), name='mcq-answer-delete'),
    path('mcq-answers/<int:user_id>/', api_views.MCQAnswersByUserView.as_view(), name='mcq-answers-by-user'),
    path('mcq-answers/non_authen/<int:user_id>/', api_views.NonAuthenTicateMCQAnswersByUserView.as_view(), name='mcq-answers-by-non-athun-user'),
    path('answer-count/<int:question_id>/', api_views.AnswerCountView.as_view(), name='answer-count'),
    
    
   
    
    # path('courses/create/', api_views.CourseViewSet.as_view({'post': 'create'}), name='course-create'),
    
    
    

    
    
    # Nitification  Routes
    
    # path("teacher/<int:teacher_id>/notification/<int:noti_id>/", api_views.TeacherNotificationDetailAPIView.as_view(), name='teacher-notification-detail'),

]


