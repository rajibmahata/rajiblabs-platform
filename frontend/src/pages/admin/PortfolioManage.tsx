import CatalogManager from "../../components/admin/CatalogManager";

export default function PortfolioManage() {
  return (
    <CatalogManager
      kind="portfolio"
      title="Portfolio"
      nameLabel="Title"
      nameKey="title"
      statuses={["draft", "review", "published", "hidden"]}
      showCategory={false}
      showProblemSolution
      showFeatures={false}
      showAiCaps
      icon="fa-briefcase"
      iconBg="var(--rla-cyan-soft)"
      iconColor="var(--rla-cyan)"
      publicPath="/portfolio"
    />
  );
}
