export default function HeroSection() {
  return (
    <section className="py-20 text-center">
      <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-400/10 border border-blue-400/20 text-blue-300 text-sm mb-8">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
        </span>
        AI-Powered Development Lab
      </div>

      <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
        Building{" "}
        <span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
          Intelligent Software
        </span>
      </h1>

      <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
        Senior Software Architect specializing in .NET, Azure, SaaS platforms,
        and AI/LLM integrations. This lab is where ideas become production-ready
        products — designed, built, tested, and deployed by an AI-guided workflow.
      </p>

      <div className="flex flex-wrap gap-3 justify-center text-sm text-gray-500">
        <span className="px-3 py-1 bg-gray-800 rounded-full">.NET 8/10</span>
        <span className="px-3 py-1 bg-gray-800 rounded-full">C#</span>
        <span className="px-3 py-1 bg-gray-800 rounded-full">React</span>
        <span className="px-3 py-1 bg-gray-800 rounded-full">Azure Cloud</span>
        <span className="px-3 py-1 bg-gray-800 rounded-full">AI / LLM</span>
        <span className="px-3 py-1 bg-gray-800 rounded-full">RAG Systems</span>
        <span className="px-3 py-1 bg-gray-800 rounded-full">Microservices</span>
        <span className="px-3 py-1 bg-gray-800 rounded-full">SaaS</span>
      </div>
    </section>
  );
}
