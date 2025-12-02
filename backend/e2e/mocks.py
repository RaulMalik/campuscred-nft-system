def inject_wallet_mock(page, address):
    """
    Injects a mock window.ethereum object into the browser.
    This tricks the frontend into thinking MetaMask is installed and connected.
    """
    mock_script = f"""
    window.ethereum = {{
        isMetaMask: true,
        request: async ({{ method }}) => {{
            console.log('Mock Ethereum call:', method);
            if (method === 'eth_requestAccounts') {{
                return ['{address}'];
            }}
            return [];
        }},
        on: (event, callback) => {{ console.log('Mock listener:', event); }}
    }};
    """
    page.add_init_script(mock_script)