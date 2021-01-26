## Homepage
1. 建立 model - Item, OrderItem, Order
2. 建立 view - HomeView 使用 ListView
3. template 用 for-loop 輸出 全部的 items，並更改所有變數
4. 分割各功能區塊，如navbar, footer, banner ，並 include 進 base.html

## User Login/Logout, Register [[link](https://django-allauth.readthedocs.io/en/latest/installation.html)]
1. pip install django-allauth
2. settings 編輯 AUTHENTICATION_BACKENDS, INSTALLED_APPS, SITE_ID, TIME_ZONE
3. 建立 urls
4. migrate
5. templates 使用

## 2. Shopping Cart
1. 新增 views: add_to_cart
2. 建立 urls，使用 slug 作為網址
3. 建立 models 的 重新導向網址
3. 使用 MDbootstrap Alert 功能

## 3. Order Summary Page
1. 新增 views: OrderSummaryView, remove_single_from_cart
2. 編輯 views: add_to_cart, remove_from_cart 在 icon 點選後的 redirect
3. 新增 urls: remove_single_from_cart
4. 新增 templates: order_summary.html
5. 編輯 templates: navbar.html 購物車連結


## 4. Checkout Page
1. 安裝 django_countries
2. 新增 forms: CheckoutForm
3. 新增 models: BillingAddress
4. 新增 views: CheckoutView
5. 新增 urls: checkout

## 5.Payment with stripe
1. 新增 views: PaymentView，編輯 views: CheckoutView
2. 新增 models: Payment
3. 更新 admin: Payment
4. 更新 settings
5. 新增 payment.html

## 6. Coupon 
1. 新增 models: Coupon
2. 新增 admin: Coupon
3. 新增 views: get_coupon, add_coupon， 修改 views: PaymentView, CheckoutView
4. 新增 forms: CouponForm
5. 新增 urls: add_coupon

## 7. Refund
1. 新增 models: Refund
2. 新增 forms: RefundForm
3. 新增 views: RequestRefundView
4. 新增 urls: request_refund
5. 新增 admin: OrderAdmin, make_refund_accepted

## 8. Default address
1. 修改 models: Address，重新makemigrations
2. 修改 views: CheckoutView
3. 新增 admin: Address
4. 修改 forms: CheckoutForm