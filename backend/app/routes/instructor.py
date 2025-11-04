from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Claim
from datetime import datetime, timedelta

bp = Blueprint('instructor', __name__, url_prefix='/instructor')


@bp.route('/dashboard')
def dashboard():
    """
    Instructor dashboard - view and manage claims
    """
    # Get all pending claims
    pending_claims = Claim.query.filter_by(status='pending').order_by(Claim.created_at.desc()).all()

    # Get recently approved claims
    approved_claims = Claim.query.filter_by(status='approved').order_by(Claim.approved_at.desc()).limit(5).all()

    # Get minted claims
    minted_claims = Claim.query.filter_by(status='minted').order_by(Claim.minted_at.desc()).limit(5).all()

    # Calculate statistics
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    stats = {
        'total_claims': Claim.query.count(),
        'pending': Claim.query.filter_by(status='pending').count(),
        'approved_week': Claim.query.filter(
            Claim.status == 'approved',
            Claim.approved_at >= one_week_ago
        ).count(),
        'total_minted': Claim.query.filter_by(status='minted').count()
    }

    return render_template(
        'instructor_dashboard.html',
        pending_claims=pending_claims,
        approved_claims=approved_claims,
        minted_claims=minted_claims,
        stats=stats
    )


@bp.route('/claim/<int:claim_id>')
def get_claim(claim_id):
    """
    Get claim details as JSON for modal view
    """
    claim = Claim.query.get_or_404(claim_id)

    return jsonify({
        'id': claim.id,
        'student_name': claim.student_name,
        'student_email': claim.student_email,
        'student_address': claim.student_address or 'N/A',
        'credential_type': claim.credential_type,
        'course_code': claim.course_code,
        'course_name': claim.description.split(':')[0] if ':' in (claim.description or '') else 'N/A',
        'description': claim.description,
        'evidence_file': claim.evidence_file_name,
        'evidence_hash': claim.evidence_file_hash,
        'status': claim.status,
        'submitted_at': claim.created_at.strftime('%Y-%m-%d %H:%M') if claim.created_at else None
    })


@bp.route('/approve/<int:claim_id>', methods=['POST'])
def approve_claim(claim_id):
    """
    Approve a claim
    Changes status from 'pending' to 'approved'
    """
    try:
        claim = Claim.query.get_or_404(claim_id)

        # Check if already approved
        if claim.status != 'pending':
            return jsonify({
                'success': False,
                'error': f'Claim is already {claim.status}'
            }), 400

        # Update claim status
        claim.status = 'approved'
        claim.approved_at = datetime.utcnow()
        claim.approved_by = 'Instructor'  # Later: get from logged-in user

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Claim #{claim_id} approved successfully!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/reject/<int:claim_id>', methods=['POST'])
def reject_claim(claim_id):
    """
    Reject a claim with reason
    Changes status from 'pending' to 'denied'
    """
    try:
        claim = Claim.query.get_or_404(claim_id)

        # Check if already processed
        if claim.status != 'pending':
            return jsonify({
                'success': False,
                'error': f'Claim is already {claim.status}'
            }), 400

        # Get rejection reason from request
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')

        # Update claim status
        claim.status = 'denied'
        claim.instructor_notes = reason
        claim.approved_by = 'Instructor'  # Who rejected it
        claim.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Claim #{claim_id} rejected'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500