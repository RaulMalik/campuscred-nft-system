from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import Claim
from app.services.storage import StorageService

bp = Blueprint('student', __name__, url_prefix='/student')
storage_service = StorageService()


@bp.route('/portal')
def portal():
    """Student portal - view and submit claims"""
    # get wallet address from session if user connected
    wallet_address = session.get('wallet_address')

    # If wallet connected, filter claims by wallet
    if wallet_address:
        claims = Claim.query.filter_by(student_address=wallet_address).order_by(Claim.created_at.desc()).all()
    else:
        # Show all claims (for demo purposes)
        claims = Claim.query.order_by(Claim.created_at.desc()).all()

    return render_template('student_portal.html', credentials=claims, wallet=wallet_address)


@bp.route('/submit-claim', methods=['POST'])
def submit_claim():
    """Handle claim submission"""
    try:
        # Get form data
        student_name = request.form.get('student_name', '').strip()
        student_email = request.form.get('student_email', '').strip()
        credential_type = request.form.get('credential_type', '').strip()
        course_code = request.form.get('course_code', '').strip()
        course_name = request.form.get('course_name', '').strip()
        description = request.form.get('description', '').strip()
        evidence_file = request.files.get('evidence')

        # get wallet address from session
        wallet_address = session.get('wallet_address')

        # Validate required fields
        if not all([student_name, student_email, credential_type, course_code]):
            flash('Please fill in all required fields!', 'danger')
            return redirect(url_for('student.portal'))

        # Validate email
        if '@' not in student_email:
            flash('Please enter a valid email address!', 'danger')
            return redirect(url_for('student.portal'))

        # Create claim
        new_claim = Claim(
            student_name=student_name,
            student_email=student_email,
            student_address=wallet_address,
            credential_type=credential_type,
            course_code=course_code.upper(),
            description=f"{course_name}: {description}" if course_name else description,
            status='pending'
        )

        db.session.add(new_claim)
        db.session.commit()

        # Handle file upload
        if evidence_file and evidence_file.filename:
            file_path, original_filename = storage_service.save_evidence_file(
                evidence_file,
                new_claim.id
            )

            if file_path:
                file_hash = Claim.compute_file_hash(file_path)
                new_claim.evidence_file_path = file_path
                new_claim.evidence_file_name = original_filename
                new_claim.evidence_file_hash = file_hash
                db.session.commit()

        success_message = f'Claim submitted successfully! Tracking ID: #{new_claim.id}'
        if wallet_address:
            success_message += 'Your wallet is connected - NFT will be minted when approved!'
        else:
            success_message += ' Connect your wallet to receive an NFT when approved.' #in case something fails

        flash(success_message, 'success')
        return redirect(url_for('student.portal'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting claim: {str(e)}', 'danger')
        return redirect(url_for('student.portal'))