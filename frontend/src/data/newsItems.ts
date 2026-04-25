// src/data/newsItems.ts
//
// Static image imports -- Vite resolves these to hashed asset URLs at build
// time. Same image (e.g. image_1_nyc.jpg) intentionally reused as both
// imageWebp and imageJpg fallback because the original assets aren't paired.
import image1Nyc from '../images/image_1_nyc.jpg';
import image2Nyc from '../images/image_2_nyc.jpg';
import image3Stock from '../images/image_3_stock.avif';
import image4Stock from '../images/image_4_stock.jpg';

export type NewsItem = {
  id: string;
  category: string;
  title: string;
  desc: string;
  date: string;        // ISO string '2025-07-01'
  readTime: string;    // '6 min read'
  href: string;        // doc/external url
  imageWebp: string;
  imageJpg: string;
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
    imageWebp: image1Nyc,
    imageJpg: image1Nyc,
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
    imageWebp: image2Nyc,
    imageJpg: image2Nyc,
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
    imageWebp: image3Stock,
    imageJpg: image4Stock,
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
    imageWebp: image4Stock,
    imageJpg: image4Stock,
    alt: "Volunteer day at a local community center"
  }
];
