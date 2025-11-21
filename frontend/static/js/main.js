// Global wallet state
let currentWallet = null;
let isConnecting = false;

// Theme Switcher
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    // Load saved theme or default to dark
    const currentTheme = localStorage.getItem('theme') || 'dark';
    html.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    // Toggle theme on button click
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);

            // Add a little animation
            this.style.transform = 'rotate(360deg)';
            setTimeout(() => {
                this.style.transform = 'rotate(0deg)';
            }, 300);
        });
    }

    function updateThemeIcon(theme) {
        const icon = themeToggle?.querySelector('i');
        if (icon) {
            if (theme === 'dark') {
                icon.className = 'fas fa-sun';
            } else {
                icon.className = 'fas fa-moon';
            }
        }
    }

    // Check session on page load
    checkWalletSession();
});

// Check if wallet is already connected (session)
async function checkWalletSession() {
    try {
        const response = await fetch('/auth/check-session');
        const data = await response.json();
        
        if (data.connected) {
            currentWallet = data.address;
            updateWalletUI(data.address, data.is_instructor);
        }
    } catch (error) {
        console.error('Error checking session:', error);
    }
}

// Wallet Connection with MetaMask
document.addEventListener('DOMContentLoaded', function() {
    const connectWalletBtns = document.querySelectorAll('#connectWalletBtn, .btn-connect-wallet');

    connectWalletBtns.forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            await connectWallet();
        });
    });
});

async function connectWallet() {
    if (isConnecting) return;
    
    // Check if MetaMask is installed
    if (typeof window.ethereum === 'undefined') {
        showToast('Please install MetaMask to connect your wallet', 'warning');
        window.open('https://metamask.io/download/', '_blank');
        return;
    }

    isConnecting = true;
    showToast('Connecting to MetaMask...', 'info');

    try {
        // Request account access
        const accounts = await window.ethereum.request({ 
            method: 'eth_requestAccounts' 
        });
        
        const address = accounts[0];
        console.log('Connected wallet:', address);

        // Send to backend to check if instructor or student
        const response = await fetch('/auth/connect-wallet', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ address: address })
        });

        const data = await response.json();

        if (data.success) {
            currentWallet = address;
            updateWalletUI(address, data.is_instructor);
            
            const role = data.is_instructor ? 'Instructor' : 'Student';
            showToast(`Connected as ${role}! Redirecting...`, 'success');
            
            // Redirect after short delay
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1500);
        } else {
            showToast(data.error || 'Failed to connect wallet', 'danger');
        }

    } catch (error) {
        console.error('Error connecting wallet:', error);
        
        if (error.code === 4001) {
            showToast('Wallet connection rejected', 'warning');
        } else {
            showToast('Failed to connect wallet: ' + error.message, 'danger');
        }
    } finally {
        isConnecting = false;
    }
}

// Update UI after wallet connection
function updateWalletUI(address, isInstructor) {
    const connectBtns = document.querySelectorAll('#connectWalletBtn, .btn-connect-wallet');
    const shortAddress = `${address.slice(0, 6)}...${address.slice(-4)}`;
    
    connectBtns.forEach(btn => {
        btn.innerHTML = `
            <i class="fas fa-wallet me-2"></i>
            ${shortAddress}
            ${isInstructor ? '<span class="badge bg-warning ms-2">Instructor</span>' : ''}
        `;
        btn.classList.add('btn-success');
        btn.classList.remove('btn-primary');
        
        // Add disconnect functionality
        btn.onclick = async (e) => {
            e.preventDefault();
            await disconnectWallet();
        };
    });
}

// Disconnect wallet
async function disconnectWallet() {
    try {
        const response = await fetch('/auth/disconnect', {
            method: 'POST'
        });
        
        if (response.ok) {
            currentWallet = null;
            showToast('Wallet disconnected', 'success');
            
            // Reset UI
            const connectBtns = document.querySelectorAll('#connectWalletBtn, .btn-connect-wallet');
            connectBtns.forEach(btn => {
                btn.innerHTML = '<i class="fas fa-wallet me-2"></i>Connect Wallet';
                btn.classList.remove('btn-success');
                btn.classList.add('btn-primary');
                btn.onclick = connectWallet;
            });
            
            // Redirect to home after short delay
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        }
    } catch (error) {
        console.error('Error disconnecting:', error);
        showToast('Error disconnecting wallet', 'danger');
    }
}

// Listen for account changes in MetaMask
if (window.ethereum) {
    window.ethereum.on('accountsChanged', function (accounts) {
        if (accounts.length === 0) {
            // User disconnected wallet
            disconnectWallet();
        } else if (currentWallet && accounts[0].toLowerCase() !== currentWallet.toLowerCase()) {
            // User switched accounts
            showToast('Wallet account changed. Please reconnect.', 'warning');
            disconnectWallet();
        }
    });

    window.ethereum.on('chainChanged', function (chainId) {
        // Reload page on network change
        window.location.reload();
    });
}

// Toast Notifications (Utility)
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');

    if (!toastContainer) {
        console.warn('Toast container not found');
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    // Remove after hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Export for use in other files
window.connectWallet = connectWallet;
window.disconnectWallet = disconnectWallet;
window.showToast = showToast;
window.currentWallet = () => currentWallet;