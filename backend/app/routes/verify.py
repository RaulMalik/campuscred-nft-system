from flask import Blueprint, render_template, request, jsonify, current_app
from app.models import Claim
from app.services.blockchain import BlockchainService
from app.services.ipfs import IPFSService
import secrets
import time

bp = Blueprint('verify', __name__, url_prefix='/verify')

# store temporary verifier links, for production we can use Redis or database (speak with customer)
verifier_links = {}


@bp.route('/', endpoint='verify_home')
def verify_home():
    """Main verify page"""
    return render_template('verify.html', credential=None, error=None, show_private=False)


@bp.route('/credential/<int:token_id>')
def verify_credential(token_id):

    # Verify credential by token ID. We only show public information no PII!

    try:
        # query database for claim
        claim = Claim.query.filter_by(token_id=token_id, status='minted').first()

        if not claim:
            return render_template('verify.html',
                                   error=f'Credential with Token ID {token_id} not found',
                                   show_private=False)

        # verify on the blockchain
        try:
            blockchain_service = BlockchainService()
            verification_data = blockchain_service.verify_credential(token_id)

            if not verification_data.get('exists'):
                return render_template('verify.html',
                                       error=f'Credential not found on blockchain',
                                       show_private=False)
        except Exception as blockchain_error:
            current_app.logger.error(f"Blockchain verification error: {str(blockchain_error)}")
            # continue with database data even if blockchain check fails
            verification_data = {'exists': True, 'blockchain_error': str(blockchain_error)}

        # public credential data (NO PII)
        credential_data = {
            'token_id': token_id,
            'course_code': claim.course_code,
            'credential_type': claim.credential_type,
            'description': claim.description,
            'issued_at': claim.minted_at.strftime('%B %d, %Y') if claim.minted_at else 'Unknown',
            'owner_address': verification_data.get('owner', claim.student_address),
            'is_revoked': verification_data.get('is_revoked', False),
            'transaction_hash': claim.transaction_hash,
            'metadata_uri': claim.metadata_uri,
            'evidence_hash': claim.evidence_file_hash,
            'issuer': 'CampusCred Pilot - DTU',
            'etherscan_url': f'https://sepolia.etherscan.io/tx/{claim.transaction_hash}' if claim.transaction_hash else None
        }

        return render_template('verify.html',
                               credential=credential_data,
                               show_private=False,
                               error=None)

    except Exception as e:
        current_app.logger.error(f"Verification error: {str(e)}")
        return render_template('verify.html',
                               error=f'Error verifying credential: {str(e)}',
                               show_private=False)


@bp.route('/generate-verifier-link/<int:token_id>', methods=['POST'])
def generate_verifier_link(token_id):

    # generate the time-limited verifier link for selective PII disclosure
    # only the credential owner can generate this (we need to implement, sharable document too)
    try:
        data = request.get_json()
        wallet_address = data.get('wallet_address', '').lower()

        # we query tjis claim
        claim = Claim.query.filter_by(token_id=token_id, status='minted').first()

        if not claim:
            return jsonify({'success': False, 'error': 'Credential not found'}), 404

        #  ownership protection
        if claim.student_address and claim.student_address.lower() != wallet_address:
            return jsonify({'success': False, 'error': 'Only credential owner can generate verifier links'}), 403

        # generate secure token
        verifier_token = secrets.token_urlsafe(32)

        # store token with expiry (i have simply made it for 15 minutes, speak with customer about options etc.)
        expiry_time = time.time() + (15 * 60)
        verifier_links[verifier_token] = {
            'token_id': token_id,
            'claim_id': claim.id,
            'expires_at': expiry_time
        }

        # clean up expired links
        _cleanup_expired_links()

        verifier_url = f'/verify/private/{verifier_token}'

        return jsonify({
            'success': True,
            'verifier_url': verifier_url,
            'expires_in': 900  # 15 minutes in seconds
        })

    except Exception as e:
        current_app.logger.error(f"Error generating verifier link: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/private/<verifier_token>')
def view_private_credential(verifier_token):

    # view credential with PII using timelimited verifier link

    try:
        # check if token exists and is valid!
        if verifier_token not in verifier_links:
            return render_template('verify.html',
                                   error='Invalid or expired verifier link',
                                   show_private=False)

        link_data = verifier_links[verifier_token]

        # check the expiry also
        if time.time() > link_data['expires_at']:
            del verifier_links[verifier_token]
            return render_template('verify.html',
                                   error='This verifier link has expired (15 minutes)',
                                   show_private=False)

        # thereafter we can get claim data
        claim = Claim.query.get(link_data['claim_id'])

        if not claim:
            return render_template('verify.html',
                                   error='Credential not found',
                                   show_private=False)

        #  FULL credential data including PII
        credential_data = {
            'token_id': claim.token_id,
            'course_code': claim.course_code,
            'credential_type': claim.credential_type,
            'description': claim.description,
            'issued_at': claim.minted_at.strftime('%B %d, %Y') if claim.minted_at else 'Unknown',
            'owner_address': claim.student_address,
            'transaction_hash': claim.transaction_hash,
            'metadata_uri': claim.metadata_uri,
            'evidence_hash': claim.evidence_file_hash,
            'issuer': 'CampusCred Pilot - DTU',
            # PII (only shown via verifier link)
            'student_name': claim.student_name,
            'student_email': claim.student_email,
            'evidence_file_name': claim.evidence_file_name,
            'etherscan_url': f'https://sepolia.etherscan.io/tx/{claim.transaction_hash}' if claim.transaction_hash else None,
            # time remaining
            'expires_in': int(link_data['expires_at'] - time.time())
        }

        return render_template('verify.html',
                               credential=credential_data,
                               show_private=True,
                               verifier_token=verifier_token,
                               error=None)

    except Exception as e:
        current_app.logger.error(f"Error viewing private credential: {str(e)}")
        return render_template('verify.html',
                               error=str(e),
                               show_private=False)


def _cleanup_expired_links():
    """Remove expired verifier links"""
    current_time = time.time()
    expired_tokens = [token for token, data in verifier_links.items()
                      if current_time > data['expires_at']]
    for token in expired_tokens:
        del verifier_links[token]