// src/data/newsItems.ts
export type NewsItem = {
  id: string;
  category: string;
  title: string;
  desc: string;
  date: string;        // ISO string '2025-07-01'
  readTime: string;    // '6 min read'
  href: string;        // doc/external url
  imageWebp: any;      // import path to .webp
  imageJpg: any;       // import path to .jpg fallback
  alt: string;
};

export const newsItems: NewsItem[] = [
  {
    id: "risk-insights-sarah-chen",
    category: "Risk Insights",
    title: "A Conversation with Dr. Sarah Chen",
    desc: "Leading quantitative researcher discusses market volatility.",
    date: "2025-06-14",
    readTime: "7 min read",
    href: "/articles/sarah-chen-interview",
    imageWebp: require("../images/image_1_nyc.jpg"),
    imageJpg: require("../images/image_1_nyc.jpg"),
    alt: "Portrait of Dr. Sarah Chen during an interview"
  },
  {
    id: "internship-experience",
    category: "Internship",
    title: "Learning from Extraordinary Colleagues",
    desc: "Summer intern shares key lessons from the program.",
    date: "2025-05-29",
    readTime: "4 min read",
    href: "/articles/internship-experience",
    imageWebp: require("../images/image_2_nyc.jpg"),
    imageJpg: require("../images/image_2_nyc.jpg"),
    alt: "Group of interns collaborating in a meeting room"
  },
  {
    id: "engineering-offsite",
    category: "Engineering",
    title: "Z-Alpha Offsite: A Catalyst for Growth",
    desc: "Team offsite focused on reliability, latency and culture.",
    date: "2025-04-18",
    readTime: "5 min read",
    href: "/articles/offsite-catalyst",
    imageWebp: require("../images/image_3_stock.avif"),
    imageJpg: require("../images/image_4_stock.jpg"),
    alt: "Team members at an engineering offsite workshop"
  },
  {
    id: "community-impact",
    category: "Community Impact",
    title: "Alex on Building Stronger Communities",
    desc: "How we partner locally to create durable impact.",
    date: "2025-03-03",
    readTime: "3 min read",
    href: "/articles/community-impact-alex",
    imageWebp: require("../images/image_4_stock.jpg"),
    imageJpg: require("../images/image_4_stock.jpg"),
    alt: "Volunteer day at a local community center"
  }
];


