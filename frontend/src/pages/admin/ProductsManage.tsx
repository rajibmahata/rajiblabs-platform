import CatalogManager from "../../components/admin/CatalogManager";

export default function ProductsManage() {
  return (
    <CatalogManager
      kind="products"
      title="Products"
      nameLabel="Name"
      nameKey="name"
      statuses={["draft", "published", "featured"]}
      showCategory
      showProblemSolution={false}
      showFeatures
      showAiCaps={false}
      icon="fa-cube"
      iconBg="var(--rla-amber-soft)"
      iconColor="var(--rla-amber)"
      publicPath="/products"
    />
  );
}
