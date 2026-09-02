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
    email2: 'rajibmahata143@outlook.com',
    phone: '+91 84202 49020',
    phoneRaw: '+918420249020',
    phoneWa: '918420249020',
    phone2: '+91 91001 84730',
    phone2Raw: '+919100184730',
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
