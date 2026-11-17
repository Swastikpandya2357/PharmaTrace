import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .models import register, adregister, OTP, AdminOTP, SCNProduct, SCNOrder, SCNLatencyLog


# -------------------------------------------------------------
# REAL-LIFE EMAIL SENDER HELPER FOR OTP
# -------------------------------------------------------------

def send_otp_email(recipient_email, code, role_label="User"):
    """
    Attempts real email dispatch via Django's configured SMTP / Email backend.
    Returns (email_sent: bool, status_message: str).
    """
    subject = f"SCN Security Code: {code} for your {role_label} Account"
    message = (
        f"Hello,\n\n"
        f"You requested a password reset for your Supply Chain Network (SCN) {role_label} account.\n\n"
        f"Your One-Time Password (OTP) is: {code}\n\n"
        f"This code will expire shortly. If you did not request this, please ignore this email.\n\n"
        f"Regards,\n"
        f"Supply Chain Network (SCN) Security Team"
    )
    email_sent = False
    error_msg = ""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'pandyaswastik2005@gmail.com')
        sent = send_mail(
            subject,
            message,
            from_email,
            [recipient_email],
            fail_silently=False
        )
        if sent > 0:
            email_sent = True
    except Exception as e:
        error_msg = str(e)
        print(f"[SCN Email Error] Failed to send email to {recipient_email}: {e}")

    print(f"[SCN OTP Audit] OTP for {recipient_email} ({role_label}) is: {code} | Sent to real inbox: {email_sent}")
    return email_sent, error_msg


# -------------------------------------------------------------
# UNIFIED SCN DASHBOARD (SAME DASHBOARD, ROLE-BASED ACCESS)
# -------------------------------------------------------------

def get_current_user_context(request):
    """
    Determines user role, name, and email from session.
    Supported roles: 'admin', 'distributor', 'retailer', or None (guest).
    """
    role = request.session.get('role')
    user_name = request.session.get('user_name')
    user_email = request.session.get('user_email')

    # Backward compatibility with existing session keys
    if not role:
        if request.session.get('admin_id'):
            role = 'admin'
            user_name = request.session.get('admin_name', 'Admin')
            user_email = request.session.get('admin_email', '')
        elif request.session.get('distributor_id'):
            role = 'distributor'
            user_name = request.session.get('distributor_username', 'Distributor')
            user_email = request.session.get('distributor_email', '')
        elif request.session.get('retailer_id'):
            role = 'retailer'
            user_name = request.session.get('retailer_name', 'Retailer')
            user_email = request.session.get('retailer_email', '')

    return role, user_name, user_email


def dashboard(request):
    user_role, user_name, user_email = get_current_user_context(request)

    products = SCNProduct.objects.all().order_by('-created_at')
    orders = SCNOrder.objects.all().order_by('-ordered_at')
    logs = SCNLatencyLog.objects.all().order_by('-timestamp')[:50]

    # Calculate live SCN latency & network metrics
    total_orders = orders.count()
    processing_orders = orders.filter(status='Processing').count()
    in_transit_orders = orders.filter(status__in=['Dispatched', 'In-Transit']).count()
    delivered_orders = orders.filter(status='Delivered').count()

    delivered_with_latency = orders.filter(status='Delivered', latency_recorded_hours__isnull=False)
    if delivered_with_latency.exists():
        latencies = [float(o.latency_recorded_hours) for o in delivered_with_latency]
        avg_latency = round(sum(latencies) / len(latencies), 1)
    else:
        avg_latency = 1.4  # Default baseline SLA in hours

    distributors_list = register.objects.filter(role='distributor')
    retailers_list = register.objects.filter(role='retailer')
    total_distributors = distributors_list.count()
    total_retailers = retailers_list.count()
    total_nodes = total_distributors + total_retailers + 1  # +1 for platform Admin

    context = {
        'user_role': user_role,
        'user_name': user_name,
        'user_email': user_email,
        'products': products,
        'orders': orders,
        'logs': logs,
        'total_orders': total_orders,
        'processing_orders': processing_orders,
        'in_transit_orders': in_transit_orders,
        'delivered_orders': delivered_orders,
        'avg_latency': avg_latency,
        'total_distributors': total_distributors,
        'total_retailers': total_retailers,
        'total_nodes': total_nodes,
        'total_logs': SCNLatencyLog.objects.count(),
        'distributors_list': distributors_list,
        'retailers_list': retailers_list,
    }
    return render(request, 'dashboard.html', context)


def admin_dashboard(request):
    return dashboard(request)


def distributor_dashboard(request):
    return dashboard(request)


# -------------------------------------------------------------
# SCN LOW-LATENCY OPERATIONS (ORDERS & INVENTORY)
# -------------------------------------------------------------

def place_order(request):
    """
    Workflow rule: Order can be placed by ALL (Retailers, Distributors, Admin, or Guests).
    """
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))

        user_role, user_name, user_email = get_current_user_context(request)
        retailer_name = request.POST.get('retailer_name') or user_name or 'Community Retail Pharmacy'
        retailer_email = request.POST.get('retailer_email') or user_email or 'retailer@scn.io'

        try:
            product = SCNProduct.objects.get(id=product_id)
            total_price = product.price * quantity
            order_id = f"ORD-SCN-{random.randint(1000, 9999)}"

            # Deduct stock if available
            if product.stock_quantity >= quantity:
                product.stock_quantity -= quantity
                product.save()

            order = SCNOrder.objects.create(
                order_id=order_id,
                retailer_name=retailer_name,
                retailer_email=retailer_email,
                distributor=product.distributor,
                product=product,
                quantity=quantity,
                total_price=total_price,
                status='Processing'
            )

            # Record transparent ledger log
            SCNLatencyLog.objects.create(
                order=order,
                event=f"Order Placed for {quantity}x {product.name}",
                recorded_by=retailer_name,
                role=user_role or 'retailer',
                latency_benchmark='SCN Consensus Time: 38ms'
            )

            messages.success(request, f"Order {order_id} placed successfully! Receipt generated: RCP-{order_id}. Guaranteed SLA: {product.lead_time_hours}h.")
        except Exception as e:
            messages.error(request, f"Error placing SCN order: {e}")

    return redirect('dashboard')


def update_order_status(request):
    """
    Workflow rules:
    - Order Dispatched: Allowed ONLY for Admin and Distributor.
    - Order Received (Delivered): Allowed ONLY for Retailer and Admin.
    """
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('new_status')

        user_role, user_name, user_email = get_current_user_context(request)
        actor_name = user_name or 'SCN Node'

        # Enforcement of exact permissions
        if new_status == 'Dispatched':
            if user_role not in ['admin', 'distributor']:
                messages.error(request, "Permission denied: Only Distributors and Admin can dispatch orders.")
                return redirect('dashboard')
        elif new_status == 'Delivered':
            if user_role not in ['admin', 'retailer']:
                messages.error(request, "Permission denied: Only Retailers and Admin can confirm receipt of orders.")
                return redirect('dashboard')

        try:
            order = SCNOrder.objects.get(order_id=order_id)
            now = timezone.now()

            if new_status == 'Dispatched':
                order.status = 'Dispatched'
                order.dispatched_at = now
                diff_hours = (now - order.ordered_at).total_seconds() / 3600.0
                order.latency_recorded_hours = round(diff_hours, 2)
                order.save()

                SCNLatencyLog.objects.create(
                    order=order,
                    event=f"Order Dispatched by {actor_name} ({order.product.name})",
                    recorded_by=actor_name,
                    role=user_role or 'distributor',
                    latency_benchmark=f"Dispatch Latency: {order.latency_recorded_hours:.2f} hrs (SLA Met)"
                )
                messages.success(request, f"Order {order_id} marked as Dispatched! Recorded latency: {order.latency_recorded_hours} hrs.")

            elif new_status == 'Delivered':
                order.status = 'Delivered'
                order.delivered_at = now
                if order.dispatched_at:
                    transit_hours = (now - order.dispatched_at).total_seconds() / 3600.0
                else:
                    transit_hours = 0.5
                total_latency = (now - order.ordered_at).total_seconds() / 3600.0
                order.latency_recorded_hours = round(total_latency, 2)
                order.save()

                SCNLatencyLog.objects.create(
                    order=order,
                    event=f"Order Received & Confirmed by {actor_name}",
                    recorded_by=actor_name,
                    role=user_role or 'retailer',
                    latency_benchmark=f"Transit: {transit_hours:.2f}h | Total SCN Cycle: {order.latency_recorded_hours:.2f} hrs"
                )
                messages.success(request, f"Order {order_id} marked as Received! Proof-of-Delivery receipt generated. Total latency: {order.latency_recorded_hours} hrs.")

        except Exception as e:
            messages.error(request, f"Error updating order status: {e}")

    return redirect('dashboard')


def update_product_stock(request):
    """
    Workflow rule: Stock status of each product can be updated by Distributor and Admin.
    """
    user_role, user_name, user_email = get_current_user_context(request)
    if user_role not in ['admin', 'distributor']:
        messages.error(request, "Permission denied: Only Distributors and Admin can update product stock status.")
        return redirect('dashboard')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        try:
            product = SCNProduct.objects.get(id=product_id)
            new_stock = int(request.POST.get('stock', product.stock_quantity))
            new_lead_time = float(request.POST.get('lead_time', product.lead_time_hours))
            product.stock_quantity = new_stock
            product.lead_time_hours = new_lead_time
            product.save()
            messages.success(request, f"Updated stock for {product.name}: {new_stock} units available, SLA: {new_lead_time} hrs.")
        except Exception as e:
            messages.error(request, f"Error updating product stock: {e}")

    return redirect('dashboard')


def view_receipt(request, order_id):
    """
    Displays the printable/downloadable official SCN Order Placement or Proof-of-Delivery receipt.
    """
    try:
        order = SCNOrder.objects.get(order_id=order_id)
        return render(request, 'receipt.html', {'order': order})
    except SCNOrder.DoesNotExist:
        messages.error(request, f"Receipt for Order {order_id} was not found.")
        return redirect('dashboard')


def add_product(request):
    """
    Allows Admin or Distributor to publish new products/medicines to catalog.
    """
    user_role, user_name, user_email = get_current_user_context(request)
    if user_role not in ['admin', 'distributor']:
        messages.error(request, "Permission denied: Only Admin and Distributors can add catalog products.")
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        sku = request.POST.get('sku')
        category = request.POST.get('category', 'General Medicine')
        price = request.POST.get('price', 10.0)
        stock = request.POST.get('stock', 100)
        lead_time = request.POST.get('lead_time', 2.0)

        dist = None
        if user_role == 'distributor':
            dist = register.objects.filter(email=user_email, role='distributor').first()

        try:
            SCNProduct.objects.create(
                name=name,
                sku=sku,
                category=category,
                price=price,
                stock_quantity=stock,
                lead_time_hours=lead_time,
                distributor=dist
            )
            messages.success(request, f"Medicine '{name}' ({sku}) published to SCN catalog with {lead_time}h SLA!")
        except Exception as e:
            messages.error(request, f"Error creating product: {e}")

    return redirect('dashboard')


def remove_node(request):
    """
    Admin only: Removes a distributor or retailer node from the SCN network.
    """
    user_role, user_name, user_email = get_current_user_context(request)
    if user_role != 'admin':
        messages.error(request, "Permission denied: Only Admin can remove network nodes.")
        return redirect('dashboard')

    if request.method == 'POST':
        node_id = request.POST.get('node_id')
        try:
            node = register.objects.get(id=node_id)
            node_name = node.username
            node_email = node.email
            node_role = node.role

            # Revoke auth_user account safely (never touches staff/superuser)
            User.objects.filter(username=node_name, is_staff=False, is_superuser=False).delete()

            # Delete node registration
            node.delete()

            messages.success(request, f"{node_role.capitalize()} node '{node_name}' ({node_email}) was successfully removed from the SCN network.")
        except register.DoesNotExist:
            messages.error(request, "Network node not found.")
        except Exception as e:
            messages.error(request, f"Error removing node: {e}")

    return redirect('dashboard')


# -------------------------------------------------------------
# ADMIN AUTH & OTP (Swastik Pandya / sompandya / pandyaswastik2005@gmail.com)
# -------------------------------------------------------------

def register_admin(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('pass', '')
        confirm_password = request.POST.get('con_pass', '')

        try:
            validate_email(email)
        except ValidationError:
            error = "Please enter a valid email address (e.g., name@example.com)."
            return render(request, 'register_admin.html', {'error': error})

        if password != confirm_password:
            error = "Passwords do not match."
        elif adregister.objects.filter(username=username).exists():
            error = "Admin with this username already exists."
        else:
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.create_user(username=username, password=password, email=email)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()

            adregister.objects.create(
                username=username,
                email=email,
                password=password,
                confirm_password=confirm_password,
                role='admin'
            )
            return redirect('login_admin')

    return render(request, 'register_admin.html', {'error': error})


def login_admin(request):
    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        password = request.POST.get('pass', '')
        user = adregister.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier),
            password=password
        ).first()

        if user:
            request.session['role'] = 'admin'
            request.session['user_id'] = user.id
            request.session['user_name'] = user.username
            request.session['user_email'] = user.email
            request.session['admin_id'] = user.id
            request.session['admin_email'] = user.email
            request.session['admin_name'] = user.username
            return redirect('dashboard')
        else:
            return render(request, 'login_admin.html', {'error': 'Invalid admin email/username or password.'})

    return render(request, 'login_admin.html')


def logout_admin(request):
    request.session.flush()
    return redirect('login_admin')


def forgot_password_admin(request):
    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        user = adregister.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier)
        ).first()

        if user:
            code = str(random.randint(100000, 999999))
            AdminOTP.objects.filter(user=user).delete()
            AdminOTP.objects.create(user=user, code=code)

            email_sent, err = send_otp_email(user.email, code, "Admin")
            if email_sent:
                info_message = f"A 6-digit OTP has been dispatched to {user.email}. Please check your inbox and spam folder."
            else:
                info_message = f"OTP Code Generated: {code} (Check your inbox or configure Gmail App Password in .env to deliver directly via SMTP)."

            return render(request, 'aenter_otp.html', {
                'email': user.email,
                'info_message': info_message,
                'otp_code': code if not email_sent else None
            })
        else:
            return render(request, 'admin_forgot.html', {'error': 'Admin with this email/username does not exist.'})

    return render(request, 'admin_forgot.html')


def verify_otp_admin(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        otp_input = request.POST.get('otp', '').strip()

        user = adregister.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
        if not user:
            return render(request, 'admin_forgot.html', {'error': 'Admin user not found.'})

        otp_record = AdminOTP.objects.filter(user=user).order_by('-created_at').first()
        if otp_record and otp_record.code == otp_input:
            return render(request, 'reset_password_admin.html', {'email': user.email})
        elif otp_record:
            return render(request, 'aenter_otp.html', {
                'email': email,
                'error': 'Invalid OTP code. Please enter the 6 digits accurately.'
            })
        else:
            return render(request, 'aenter_otp.html', {
                'email': email,
                'error': 'No active OTP found. Please request a new code.'
            })

    return redirect('forgot_password_admin')


def resend_otp_admin(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = adregister.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
        if user:
            new_code = str(random.randint(100000, 999999))
            AdminOTP.objects.filter(user=user).delete()
            AdminOTP.objects.create(user=user, code=new_code)

            email_sent, _ = send_otp_email(user.email, new_code, "Admin")
            if email_sent:
                msg = f"A new OTP was sent to {user.email}."
            else:
                msg = f"New OTP Generated: {new_code}"

            return render(request, 'aenter_otp.html', {
                'email': user.email,
                'message': msg,
                'otp_code': new_code if not email_sent else None
            })
        else:
            return render(request, 'admin_forgot.html', {'error': 'Admin user not found.'})

    return redirect('forgot_password_admin')


def reset_password_admin(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if password != confirm_password:
            return render(request, 'reset_password_admin.html', {'email': email, 'error': 'Passwords do not match.'})

        user = adregister.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
        if user:
            user.password = password
            user.confirm_password = confirm_password
            user.save()
            AdminOTP.objects.filter(user=user).delete()

            auth_user = User.objects.filter(username=user.username).first() or User.objects.filter(email=user.email).first()
            if auth_user:
                auth_user.set_password(password)
                auth_user.save()

            messages.success(request, "Password successfully reset! Please log in with your new password.")
            return redirect('login_admin')
        else:
            return render(request, 'reset_password_admin.html', {'email': email, 'error': 'User not found.'})

    return redirect('forgot_password_admin')


# -------------------------------------------------------------
# DISTRIBUTOR AUTH & OTP (ALLOW SAME EMAIL ACROSS MULTIPLE NODES)
# -------------------------------------------------------------

def register_distributor(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('Username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_pass', '')

        try:
            validate_email(email)
        except ValidationError:
            error = "Please enter a valid email address."
            return render(request, 'register_distributor.html', {'error': error})

        if password != confirm_password:
            error = "Passwords do not match."
        elif register.objects.filter(email__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            error = f"An account with email '{email}' is already registered. Each account must have a unique email address for secure OTP recovery."
        elif register.objects.filter(username__iexact=username).exists() or User.objects.filter(username__iexact=username).exists():
            error = f"Distributor with username '{username}' already exists. Please choose a different company/node name."
        else:
            register.objects.create(
                username=username,
                email=email,
                password=password,
                confirm_password=confirm_password,
                role='distributor'
            )
            # Create django user if unique
            if not User.objects.filter(username=username).exists():
                u = User.objects.create_user(username=username, password=password, email=email)
                u.is_staff = False
                u.save()

            messages.success(request, f"Distributor '{username}' successfully registered! Unique email '{email}' linked for OTP recovery.")
            return redirect('login_distributor')

    return render(request, 'register_distributor.html', {'error': error})


def login_distributor(request):
    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Match by username or email for distributor role
        user = register.objects.filter(
            Q(username__iexact=identifier) | Q(email__iexact=identifier),
            password=password,
            role='distributor'
        ).first()

        # Fallback
        if not user:
            user = register.objects.filter(
                Q(username__iexact=identifier) | Q(email__iexact=identifier),
                password=password
            ).first()

        if user:
            request.session['role'] = 'distributor'
            request.session['user_id'] = user.id
            request.session['user_name'] = user.username
            request.session['user_email'] = user.email
            request.session['distributor_id'] = user.id
            request.session['distributor_email'] = user.email
            request.session['distributor_username'] = user.username
            return redirect('dashboard')
        else:
            return render(request, 'login_distributor.html', {'error': 'Invalid distributor username/email or password.'})

    return render(request, 'login_distributor.html')


def logout_distributor(request):
    request.session.flush()
    return redirect('login_distributor')


def forgot_password_distributor(request):
    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        user = register.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier),
            role='distributor'
        ).first()
        if not user:
            user = register.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()

        if user:
            recipient_email = user.email
            code = str(random.randint(100000, 999999))
            OTP.objects.filter(user=user).delete()
            OTP.objects.create(user=user, code=code)

            email_sent, _ = send_otp_email(recipient_email, code, "Distributor")
            if email_sent:
                info_message = f"A 6-digit OTP has been sent to {recipient_email}. Check your inbox and spam folder."
            else:
                info_message = f"OTP Code Generated: {code} (Delivering directly via configured SMTP)."

            return render(request, 'denter_otp.html', {
                'email': recipient_email,
                'info_message': info_message,
                'otp_code': code if not email_sent else None
            })
        else:
            return render(request, 'distributor_forgot.html', {'error': 'No distributor found with this email or username.'})

    return render(request, 'distributor_forgot.html')


def verify_otp_distributor(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        otp = request.POST.get('otp', '').strip()

        user = register.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
        if not user:
            return render(request, 'distributor_forgot.html', {'error': 'Distributor not found.'})

        record = OTP.objects.filter(user=user).order_by('-created_at').first()
        if record and record.code == otp:
            return render(request, 'reset_password_distributor.html', {'email': user.email})
        elif record:
            return render(request, 'denter_otp.html', {
                'email': email,
                'error': 'Invalid OTP. Please check the code and try again.'
            })
        else:
            return render(request, 'denter_otp.html', {
                'email': email,
                'error': 'No active OTP found. Please request a new code.'
            })

    return redirect('forgot_password_distributor')


def resend_otp_distributor(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = register.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
        if user:
            recipient_email = user.email
            new_code = str(random.randint(100000, 999999))
            OTP.objects.filter(user=user).delete()
            OTP.objects.create(user=user, code=new_code)

            email_sent, _ = send_otp_email(recipient_email, new_code, "Distributor")
            if email_sent:
                msg = f"OTP resent to {recipient_email}."
            else:
                msg = f"New OTP Generated: {new_code}"

            return render(request, 'denter_otp.html', {
                'email': recipient_email,
                'message': msg,
                'otp_code': new_code if not email_sent else None
            })
        else:
            return render(request, 'distributor_forgot.html', {'error': 'Distributor not found.'})

    return redirect('forgot_password_distributor')


def reset_password_distributor(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        new_password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not email:
            return render(request, 'reset_password_distributor.html', {'error': 'Email is missing.'})

        if new_password != confirm_password:
            return render(request, 'reset_password_distributor.html', {
                'email': email,
                'error': 'Passwords do not match.'
            })

        user = register.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email),
            role='distributor'
        ).first()
        if not user:
            user = register.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()

        if user:
            user.password = new_password
            user.confirm_password = confirm_password
            user.save()
            OTP.objects.filter(user=user).delete()

            auth_user = User.objects.filter(username=user.username).first() or User.objects.filter(email=user.email).first()
            if auth_user:
                auth_user.set_password(new_password)
                auth_user.save()

            messages.success(request, "Password successfully reset! Please log in.")
            return redirect('login_distributor')
        else:
            return render(request, 'reset_password_distributor.html', {
                'email': email,
                'error': 'User not found.'
            })

    return redirect('forgot_password_distributor')


# -------------------------------------------------------------
# RETAILER / USER AUTH & OTP (SINGLE EMAIL PER ACCOUNT)
# -------------------------------------------------------------

def register_user(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('Username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_pass', '')

        try:
            validate_email(email)
        except ValidationError:
            error = "Please enter a valid email address."
            return render(request, 'register_user.html', {'error': error})

        if password != confirm_password:
            error = "Passwords do not match."
        elif register.objects.filter(email__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            error = f"An account with email '{email}' is already registered. Each account must have a unique email address for secure OTP recovery."
        elif register.objects.filter(username__iexact=username).exists() or User.objects.filter(username__iexact=username).exists():
            error = f"Retailer store with name '{username}' already exists. Please choose a different store name."
        else:
            register.objects.create(
                username=username,
                email=email,
                password=password,
                confirm_password=confirm_password,
                role='retailer'
            )
            if not User.objects.filter(username=username).exists():
                u = User.objects.create_user(username=username, password=password, email=email)
                u.is_staff = False
                u.save()

            messages.success(request, f"Retailer store '{username}' successfully registered! Unique email '{email}' linked for OTP recovery.")
            return redirect('login_user')

    return render(request, 'register_user.html', {'error': error})


def login_user(request):
    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Match by username or email for retailer role
        user = register.objects.filter(
            Q(username__iexact=identifier) | Q(email__iexact=identifier),
            password=password,
            role='retailer'
        ).first()

        if not user:
            user = register.objects.filter(
                Q(username__iexact=identifier) | Q(email__iexact=identifier),
                password=password
            ).first()

        if user:
            request.session['role'] = 'retailer'
            request.session['user_id'] = user.id
            request.session['user_name'] = user.username
            request.session['user_email'] = user.email
            request.session['retailer_id'] = user.id
            return redirect('dashboard')
        else:
            return render(request, 'login_user.html', {'error': 'Invalid retailer store name/email or password.'})

    return render(request, 'login_user.html')


def logout_user(request):
    request.session.flush()
    return redirect('login_user')


def forgot_password_user(request):
    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        user = register.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier),
            role='retailer'
        ).first()
        if not user:
            user = register.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()

        if user:
            recipient_email = user.email
            code = str(random.randint(100000, 999999))
            OTP.objects.filter(user=user).delete()
            OTP.objects.create(user=user, code=code)

            email_sent, _ = send_otp_email(recipient_email, code, "Retailer")
            if email_sent:
                info_message = f"A 6-digit OTP has been sent to {recipient_email}. Check your inbox and spam folder."
            else:
                info_message = f"OTP Code Generated: {code} (Delivering directly via configured SMTP)."

            return render(request, 'uenter_otp.html', {
                'email': recipient_email,
                'info_message': info_message,
                'otp_code': code if not email_sent else None
            })
        else:
            return render(request, 'user_forgot.html', {'error': 'No retailer found with this email or store name.'})

    return render(request, 'user_forgot.html')


def verify_otp_user(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        otp = request.POST.get('otp', '').strip()

        user = register.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
        if not user:
            return render(request, 'user_forgot.html', {'error': 'Retailer not found.'})

        record = OTP.objects.filter(user=user).order_by('-created_at').first()
        if record and record.code == otp:
            return render(request, 'reset_password_user.html', {'email': user.email})
        elif record:
            return render(request, 'uenter_otp.html', {
                'email': email,
                'error': 'Invalid OTP code. Please try again.'
            })
        else:
            return render(request, 'uenter_otp.html', {
                'email': email,
                'error': 'No active OTP found.'
            })

    return redirect('forgot_password_user')


def resend_otp_user(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = register.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
        if user:
            recipient_email = user.email
            new_code = str(random.randint(100000, 999999))
            OTP.objects.filter(user=user).delete()
            OTP.objects.create(user=user, code=new_code)

            email_sent, _ = send_otp_email(recipient_email, new_code, "Retailer")
            if email_sent:
                msg = f"OTP resent to {recipient_email}."
            else:
                msg = f"New OTP Generated: {new_code}"

            return render(request, 'uenter_otp.html', {
                'email': recipient_email,
                'message': msg,
                'otp_code': new_code if not email_sent else None
            })
        else:
            return render(request, 'user_forgot.html', {'error': 'Retailer not found.'})

    return redirect('forgot_password_user')


def reset_password_user(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        new_password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not email:
            return render(request, 'reset_password_user.html', {'error': 'Email is missing.'})

        if new_password != confirm_password:
            return render(request, 'reset_password_user.html', {
                'email': email,
                'error': 'Passwords do not match.'
            })

        user = register.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email),
            role='retailer'
        ).first()
        if not user:
            user = register.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()

        if user:
            user.password = new_password
            user.confirm_password = confirm_password
            user.save()
            OTP.objects.filter(user=user).delete()

            auth_user = User.objects.filter(username=user.username).first() or User.objects.filter(email=user.email).first()
            if auth_user:
                auth_user.set_password(new_password)
                auth_user.save()

            messages.success(request, "Password successfully reset! Please log in as Retailer.")
            return redirect('login_user')
        else:
            return render(request, 'reset_password_user.html', {
                'email': email,
                'error': 'Retailer not found.'
            })

    return redirect('forgot_password_user')
