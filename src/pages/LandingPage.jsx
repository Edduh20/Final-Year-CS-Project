import { Shield, FileCheck, Users, Lock, ArrowRight, CheckCircle, FileCheck2, UserPlus } from 'lucide-react';

export default function LandingPage() {
  const handleNavigate = (path) => {
    window.location.href = path;
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex justify-start gap-2">
              <span className="text-2xl font-bold text-emerald-800">TitleGuard</span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleNavigate('/register')}
                className="hidden sm:inline-flex items-center gap-2 px-6 py-2 border-2 border-emerald-600 text-emerald-600 rounded-lg font-medium hover:bg-emerald-50 transition-colors"
              >
                <UserPlus className="w-4 h-4" />
                Register
              </button>
              <button
                onClick={() => handleNavigate('/login')}
                className="bg-emerald-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-emerald-700 transition-colors"
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h1 className="text-5xl font-bold text-slate-900 mb-6">
              Secure Land Ownership
              <span className="block text-emerald-600 mt-2">Management System</span>
            </h1>
            <p className="text-xl text-slate-600 mb-8">
              Protect your land rights with OCR verification for landowners across Kenya.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => handleNavigate('/register')}
                className="inline-flex items-center gap-2 bg-emerald-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-emerald-700 transition-colors shadow-lg hover:shadow-xl"
              >
                <UserPlus className="w-5 h-5" />
                Create Free Account
              </button>
              <button
                onClick={() => handleNavigate('/login')}
                className="inline-flex items-center gap-2 bg-white text-emerald-600 px-8 py-4 rounded-lg text-lg font-semibold border-2 border-emerald-600 hover:bg-emerald-50 transition-colors"
              >
                Sign In
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-slate-500 mt-4">
              Free for landowners • Secure • Easy to use
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-8 mb-20">
            <div className="bg-slate-50 rounded-xl p-8 hover:shadow-lg transition-shadow">
              <div className="bg-emerald-600 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <FileCheck className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Document Verification</h3>
              <p className="text-slate-600">
                Advanced OCR technology verifies title deeds and land documents instantly,
                ensuring authenticity and preventing fraud.
              </p>
            </div>

            <div className="bg-slate-50 rounded-xl p-8 hover:shadow-lg transition-shadow">
              <div className="bg-emerald-600 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <Lock className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Secure Transactions</h3>
              <p className="text-slate-600">
                Transfer land ownership with confidence through our secure platform with
                legal officer approval and M-Pesa integration.
              </p>
            </div>

            <div className="bg-slate-50 rounded-xl p-8 hover:shadow-lg transition-shadow">
              <div className="bg-emerald-600 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Role-Based Access</h3>
              <p className="text-slate-600">
                Multi-level verification system with landowners, land officers, legal officers,
                and administrators ensuring proper oversight.
              </p>
            </div>
          </div>

          {/* How It Works Section */}
          <div className="mb-20">
            <h2 className="text-3xl font-bold text-slate-900 mb-12 text-center">
              How TitleGuard Works
            </h2>
            <div className="grid md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="bg-emerald-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-emerald-600">1</span>
                </div>
                <h4 className="font-semibold text-slate-900 mb-2">Register Account</h4>
                <p className="text-sm text-slate-600">
                  Create your free account with email and ID number
                </p>
              </div>
              <div className="text-center">
                <div className="bg-emerald-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-emerald-600">2</span>
                </div>
                <h4 className="font-semibold text-slate-900 mb-2">Upload Documents</h4>
                <p className="text-sm text-slate-600">
                  Submit your title deeds for verification
                </p>
              </div>
              <div className="text-center">
                <div className="bg-emerald-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-emerald-600">3</span>
                </div>
                <h4 className="font-semibold text-slate-900 mb-2">Get Verified</h4>
                <p className="text-sm text-slate-600">
                  Land officers verify using OCR technology
                </p>
              </div>
              <div className="text-center">
                <div className="bg-emerald-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-emerald-600">4</span>
                </div>
                <h4 className="font-semibold text-slate-900 mb-2">Manage Property</h4>
                <p className="text-sm text-slate-600">
                  Transfer ownership securely when needed
                </p>
              </div>
            </div>
          </div>

          {/* Benefits Section */}
          <div className="bg-gradient-to-br from-emerald-50 to-slate-50 rounded-2xl p-12">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl font-bold text-slate-900 mb-8 text-center">
                Why Choose TitleGuard?
              </h2>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">Instant Verification</h4>
                    <p className="text-slate-600">OCR technology processes documents in seconds</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">Fraud Prevention</h4>
                    <p className="text-slate-600">Multi-layer verification prevents fake documents</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">Mobile Payments</h4>
                    <p className="text-slate-600">M-Pesa integration for seamless transactions</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">Real-Time Updates</h4>
                    <p className="text-slate-600">Get instant notifications on ownership changes</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">Secure Storage</h4>
                    <p className="text-slate-600">Bank-level encryption for all documents</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">Easy Transfers</h4>
                    <p className="text-slate-600">Transfer ownership with just a few clicks</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-emerald-600 py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Secure Your Land Rights?
          </h2>
          <p className="text-emerald-100 text-lg mb-8">
            Join thousands of landowners protecting their property with TitleGuard
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex gap-2">
              <span className="font-semibold text-emerald-800">TitleGuard</span>
            </div>
            <p className="text-slate-600 text-sm">
              © 2025 TitleGuard. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}