import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { Criteria } from "@/components/landing/Criteria";
import { DataSources } from "@/components/landing/DataSources";
import { CTA } from "@/components/landing/CTA";

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <HowItWorks />
        <Criteria />
        <DataSources />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
