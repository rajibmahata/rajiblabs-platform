// Site-wide contact configuration — single source of truth for WhatsApp, Call, Email
// Update these values to change contact options globally (PWA shortcuts, floating buttons, contact section)

export const siteConfig = {
  name: 'RajibLabs',
  domain: 'rajiblabs.com',
  url: 'https://rajiblabs.com',
  owner: 'Rajib Mahata',
  tagline: 'I build backend systems and SaaS products that scale, perform, and ship.',

  contact: {
    email: 'rajibmahata143@gmail.com',
    // Phone with country code — used for tel: and wa.me (no spaces, no + for wa.me)
    phone: '+91 98765 43210', // <-- Replace with real number
    phoneRaw: '+919876543210', // E.164 for tel:
    phoneWa: '919876543210',   // wa.me requires without + and spaces
    whatsappMessage: encodeURIComponent(
      'Hi Rajib, I visited RajibLabs and would like to discuss a project. '
    ),
    location: 'Kolkata, India · Available globally · Remote-first',
  },

  social: {
    github: 'https://github.com/rajibmahata',
    linkedin: 'https://linkedin.com/in/rajib-mahata',
  },

  // Derived links
  get whatsappLink() {
    return `https://wa.me/${this.contact.phoneWa}?text=${this.contact.whatsappMessage}`;
  },
  get callLink() {
    return `tel:${this.contact.phoneRaw}`;
  },
  get emailLink() {
    return `mailto:${this.contact.email}`;
  },
} as const;

export type SiteConfig = typeof siteConfig;
