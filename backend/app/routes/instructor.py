from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app import db
from app.models import Claim
from datetime import datetime, timedelta
from app.routes.auth import instructor_required

bp = Blueprint('instructor', __name__, url_prefix='/instructor')


@bp.route('/dashboard')
@instructor_required
def dashboard():
    """
    Instructor dashboard - view and manage claims
    """
    # get all the pending claims
    pending_claims = Claim.query.filter_by(status='pending').order_by(Claim.created_at.desc()).all()

    # recently approved claims
    approved_claims = Claim.query.filter_by(status='approved').order_by(Claim.approved_at.desc()).limit(5).all()

    # minted claims
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
@instructor_required
def get_claim(claim_id):
    """
    Get claim details as JSON for modal view
    """
    claim = Claim.query.get_or_404(claim_id)

    return jsonify({
        'id': claim.id,
        'student_name': claim.student_name,
        'student_email': claim.student_email,
        'student_address': claim.student_address or 'No wallet connected',
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
@instructor_required
def approve_claim(claim_id):
    """
    Approve a claim and mint NFT if student has wallet connected
    Changes status from 'pending' to 'approved' or 'minted'
    """
    try:
        claim = Claim.query.get_or_404(claim_id)

        # check if approved
        if claim.status != 'pending':
            return jsonify({
                'success': False,
                'error': f'Claim is already {claim.status}'
            }), 400

        # update claim status to approved
        claim.status = 'approved'
        claim.approved_at = datetime.utcnow()
        claim.approved_by = 'Instructor'
        db.session.commit()

        # Try to mint NFT if student has wallet
        if claim.student_address:
            try:
                from app.services.blockchain import BlockchainService
                from app.services.ipfs import IPFSService

                # create metadata
                ipfs_service = IPFSService()
                metadata = {
                    "name": f"{claim.course_code} - {claim.credential_type}",
                    "description": claim.description or f"Credential for {claim.course_code}",
                    "attributes": [
                        {"trait_type": "Course Code", "value": claim.course_code},
                        {"trait_type": "Credential Type", "value": claim.credential_type},
                        {"trait_type": "Issuer", "value": "CampusCred Pilot"},
                        {"trait_type": "Student", "value": claim.student_name},
                        {"trait_type": "Issued Date", "value": claim.approved_at.strftime('%Y-%m-%d')}
                    ],
                    "external_url": f"https://campuscred.app/verify/{claim.id}",
                    "evidence_hash": claim.evidence_file_hash
                }

                # Upload metadata to IPFS
                current_app.logger.info(f"Uploading metadata to IPFS for claim {claim_id}")
                metadata_uri = ipfs_service.upload_json(metadata, pin_name=f"Claim-{claim_id}")

                # mint NFT
                current_app.logger.info(f"Minting NFT for claim {claim_id}")
                blockchain_service = BlockchainService()
                token_id, tx_hash = blockchain_service.mint_credential(
                    claim.student_address,
                    metadata_uri
                )

                # Update claim with blockchain data
                claim.status = 'minted'
                claim.token_id = token_id
                claim.transaction_hash = tx_hash
                claim.metadata_uri = metadata_uri
                claim.minted_at = datetime.utcnow()
                db.session.commit()

                current_app.logger.info(f"Successfully minted NFT {token_id} for claim {claim_id}")

                return jsonify({
                    'success': True,
                    'message': f'Claim approved and NFT minted! Token ID: {token_id}',
                    'status': 'minted',
                    'token_id': token_id,
                    'tx_hash': tx_hash,
                    'etherscan_url': f'https://sepolia.etherscan.io/tx/{tx_hash}'
                })

            except Exception as mint_error:
                current_app.logger.error(f"Minting error for claim {claim_id}: {str(mint_error)}")
                # keep status as approved even if minting fails (not quite sure if it should stay approved or fail)
                return jsonify({
                    'success': True,
                    'message': f'Claim approved! Minting will be retried later.',
                    'status': 'approved',
                    'minting_error': str(mint_error)
                })
        else:
            # no wallet address, just approve
            return jsonify({
                'success': True,
                'message': 'Claim approved! Student needs to connect wallet for NFT minting.',
                'status': 'approved'
            })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving claim {claim_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/reject/<int:claim_id>', methods=['POST'])
@instructor_required
def reject_claim(claim_id):
    """
    Reject a claim with reason
    Changes status from 'pending' to 'denied'
    """
    try:
        claim = Claim.query.get_or_404(claim_id)

        # if already processed
        if claim.status != 'pending':
            return jsonify({
                'success': False,
                'error': f'Claim is already {claim.status}'
            }), 400

        # rejection reason from request
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')

        # update claim status
        claim.status = 'denied'
        claim.instructor_notes = reason
        claim.approved_by = 'Instructor'
        claim.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Claim #{claim_id} rejected'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting claim {claim_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/retry-mint/<int:claim_id>', methods=['POST'])
@instructor_required
def retry_mint(claim_id):
    """
    Retry minting for an approved claim
    """
    try:
        claim = Claim.query.get_or_404(claim_id)

        if claim.status != 'approved':
            return jsonify({
                'success': False,
                'error': f'Can only mint approved claims (current status: {claim.status})'
            }), 400

        if not claim.student_address:
            return jsonify({
                'success': False,
                'error': 'Student wallet address not available'
            }), 400

        # Attempt minting
        from app.services.blockchain import BlockchainService
        from app.services.ipfs import IPFSService

        ipfs_service = IPFSService()
        metadata = {
            "name": f"{claim.course_code} - {claim.credential_type}",
            "description": claim.description or f"Credential for {claim.course_code}",
            "attributes": [
                {"trait_type": "Course Code", "value": claim.course_code},
                {"trait_type": "Credential Type", "value": claim.credential_type},
                {"trait_type": "Issuer", "value": "CampusCred Pilot"}
            ],
            "evidence_hash": claim.evidence_file_hash
        }

        metadata_uri = ipfs_service.upload_json(metadata)

        blockchain_service = BlockchainService()
        token_id, tx_hash = blockchain_service.mint_credential(
            claim.student_address,
            metadata_uri
        )

        claim.status = 'minted'
        claim.token_id = token_id
        claim.transaction_hash = tx_hash
        claim.metadata_uri = metadata_uri
        claim.minted_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'NFT minted successfully! Token ID: {token_id}',
            'token_id': token_id,
            'tx_hash': tx_hash
        })

    except Exception as e:
        current_app.logger.error(f"Retry mint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500