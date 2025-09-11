package br.pucminas.lab;

/**
 * Lab 2: Um estudo das características de qualidade de sistemas Java
 * Laboratório de Experimentação de Software - PUC Minas
 * Professor: João Paulo Carneiro Aramuni
 * 
 * Análise de correlação entre métricas de processo e qualidade em repositórios Java
 * usando a ferramenta CK (Chidamber & Kemerer)
 * 
 * Questões de Pesquisa:
 * RQ01: Popularidade vs Qualidade (Stars vs CK metrics)
 * RQ02: Maturidade vs Qualidade (Idade vs CK metrics)  
 * RQ03: Atividade vs Qualidade (Releases vs CK metrics)
 * RQ04: Tamanho vs Qualidade (LOC vs CK metrics)
 * 
 * Sprints:
 * Lab02S01: Lista 1000 repos + Script + 1 repo teste (5pts)
 * Lab02S02: CSV completo + hipóteses + Análise e relatório final (15pts)
 */

import org.kohsuke.github.*;
import org.eclipse.jgit.api.Git;
import org.eclipse.jgit.api.errors.GitAPIException;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVPrinter;
import org.apache.commons.lang3.StringUtils;

import java.io.*;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.*;

public class Lab2JavaAnalyzer {
    
    private static final String DATA_DIR = "data";
    private static final String REPOS_DIR = "repos_cloned";
    private static final String CONFIG_FILE = "config.properties";
    private static final int MAX_REPOS_LIMIT = 100; // Aumentado para coleta completa
    
    private final GitHub github;
    private final ObjectMapper objectMapper;
    private final Path dataPath;
    private final Path reposPath;
    
    public Lab2JavaAnalyzer() throws IOException {
        // Configurar GitHub API
        Properties config = loadConfig();
        String githubToken = config.getProperty("github.token");
        if (StringUtils.isBlank(githubToken)) {
            throw new IllegalStateException("GitHub token não configurado em config.properties");
        }
        
        this.github = new GitHubBuilder().withOAuthToken(githubToken).build();
        this.objectMapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);
        
        // Criar diretórios
        this.dataPath = Paths.get(DATA_DIR);
        this.reposPath = Paths.get(REPOS_DIR);
        Files.createDirectories(dataPath);
        Files.createDirectories(reposPath);
        
        System.out.println("Lab 2 Java Analyzer inicializado");
        System.out.println("Diretório de dados: " + dataPath.toAbsolutePath());
        System.out.println("Diretório de repos: " + reposPath.toAbsolutePath());
    }
    
    private Properties loadConfig() throws IOException {
        Properties config = new Properties();
        Path configPath = Paths.get(CONFIG_FILE);
        
        if (!Files.exists(configPath)) {
            // Criar arquivo de config de exemplo
            try (PrintWriter writer = new PrintWriter(Files.newBufferedWriter(configPath))) {
                writer.println("# Configuração do Lab 2");
                writer.println("# GitHub Personal Access Token");
                writer.println("# Obtenha em: https://github.com/settings/tokens");
                writer.println("github.token=SEU_TOKEN_AQUI");
                writer.println("");
                writer.println("# Configurações opcionais");
                writer.println("max.repos=1000");
                writer.println("clone.timeout=300");
            }
            throw new FileNotFoundException("Arquivo config.properties criado. Configure seu GitHub token!");
        }
        
        try (InputStream input = Files.newInputStream(configPath)) {
            config.load(input);
        }
        return config;
    }
    
    /**
     * Lab02S01: Coleta dos top-1000 repositórios Java mais populares
     */
    public void executeLab02S01() {
        System.out.println("\n=== EXECUTANDO LAB02S01 ===");
        System.out.println("Coletando top-1000 repositórios Java mais populares...");
        
        try {
            List<RepositoryInfo> repositories = collectTop1000JavaRepos();
            
            // Salvar JSON
            Path jsonFile = dataPath.resolve("repositorios_1000_java.json");
            objectMapper.writeValue(jsonFile.toFile(), repositories);
            
            // Salvar CSV básico
            Path csvFile = dataPath.resolve("repositorios_1000_java.csv");
            saveRepositoriesCSV(repositories, csvFile);
            
            // Testar com 1 repositório
            if (!repositories.isEmpty()) {
                System.out.println("\nTestando análise CK com 1 repositório...");
                RepositoryInfo testRepo = repositories.get(0);
                testSingleRepository(testRepo);
            }
            
            System.out.println("\nLAB02S01 CONCLUÍDO!");
            System.out.println("Arquivos gerados:");
            System.out.println("- " + jsonFile.toAbsolutePath());
            System.out.println("- " + csvFile.toAbsolutePath());
            
        } catch (Exception e) {
            System.err.println("ERRO no LAB02S01: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * Lab02S02: Análise completa dos 1000 repositórios com métricas CK
     */
    public void executeLab02S02() {
        System.out.println("\n=== EXECUTANDO LAB02S02 ===");
        
        try {
            // Carregar lista de repositórios
            Path jsonFile = dataPath.resolve("repositorios_1000_java.json");
            if (!Files.exists(jsonFile)) {
                System.err.println("ERRO: Execute primeiro LAB02S01!");
                return;
            }
            
            List<RepositoryInfo> repositories = Arrays.asList(
                objectMapper.readValue(jsonFile.toFile(), RepositoryInfo[].class)
            );
            
            System.out.println("Processando " + repositories.size() + " repositórios...");
            
            List<RepositoryAnalysis> results = new ArrayList<>();
            int processed = 0;
            
            for (RepositoryInfo repo : repositories) {
                if (processed >= MAX_REPOS_LIMIT) {
                    System.out.println("AVISO: Limite de processamento atingido: " + processed + " repositórios");
                    break;
                }
                
                try {
                    System.out.printf("[%d/%d] Analisando: %s\n", processed + 1, 
                        Math.min(repositories.size(), MAX_REPOS_LIMIT), repo.fullName);
                    
                    RepositoryAnalysis analysis = analyzeRepository(repo);
                    if (analysis != null) {
                        results.add(analysis);
                        System.out.printf("  SUCESSO: CBO=%.1f, DIT=%.1f, LCOM=%.1f\n", 
                            analysis.cboMean, analysis.ditMean, analysis.lcomMean);
                    } else {
                        System.out.println("  PULADO: Erro na análise");
                    }
                    
                    processed++;
                    
                    // Salvar progresso a cada 10 repositórios
                    if (processed % 10 == 0) {
                        saveResultsCSV(results, dataPath.resolve("progresso_lab02s02.csv"));
                        System.out.println("  SALVO: " + processed + " repositórios processados");
                    }
                    
                } catch (Exception e) {
                    System.out.println("  ERRO: " + e.getMessage());
                }
            }
            
            if (!results.isEmpty()) {
                // Salvar resultado final
                Path finalFile = dataPath.resolve("lab02s02_final_java.csv");
                saveResultsCSV(results, finalFile);
                
                System.out.println("\nLAB02S02 CONCLUÍDO!");
                System.out.println("Resultado final: " + finalFile.toAbsolutePath());
                System.out.println("Repositórios analisados: " + results.size());
                
                printQuickStats(results);
            } else {
                System.err.println("ERRO: Nenhum repositório foi processado com sucesso!");
            }
            
        } catch (Exception e) {
            System.err.println("ERRO no LAB02S02: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    private List<RepositoryInfo> collectTop1000JavaRepos() throws IOException {
        System.out.println("Buscando repositórios Java no GitHub...");
        
        List<RepositoryInfo> repositories = new ArrayList<>();
        
        // Buscar repositórios Java ordenados por estrelas
        GHRepositorySearchBuilder search = github.searchRepositories()
            .language("java")
            .sort(GHRepositorySearchBuilder.Sort.STARS)
            .order(GHDirection.DESC);
        
        PagedSearchIterable<GHRepository> searchResult = search.list();
        
        int count = 0;
        for (GHRepository repo : searchResult) {
            if (count >= 1000) break;
            
            try {
                RepositoryInfo info = new RepositoryInfo();
                info.fullName = repo.getFullName();
                info.name = repo.getName();
                info.owner = repo.getOwner().getLogin();
                info.description = repo.getDescription();
                info.stars = repo.getStargazersCount();
                info.forks = repo.getForksCount();
                info.size = repo.getSize();
                info.language = repo.getLanguage();
                LocalDateTime created = repo.getCreatedAt().toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
                LocalDateTime updated = repo.getUpdatedAt().toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
                info.createdAt = created.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
                info.updatedAt = updated.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
                info.hasIssues = repo.hasIssues();
                info.hasWiki = repo.hasWiki();
                info.defaultBranch = repo.getDefaultBranch();
                info.cloneUrl = repo.getHttpTransportUrl();
                
                // Calcular idade em anos
                info.ageInYears = ChronoUnit.YEARS.between(created, LocalDateTime.now());
                
                // Contar releases
                try {
                    info.releasesCount = repo.listReleases().toList().size();
                } catch (Exception e) {
                    info.releasesCount = 0;
                }
                
                repositories.add(info);
                count++;
                
                if (count % 100 == 0) {
                    System.out.println("Coletados: " + count + " repositórios");
                }
                
            } catch (Exception e) {
                System.out.println("Erro ao processar repo " + repo.getFullName() + ": " + e.getMessage());
            }
        }
        
        System.out.println("Total de repositórios coletados: " + repositories.size());
        return repositories;
    }
    
    private void testSingleRepository(RepositoryInfo repo) {
        System.out.println("Testando análise CK no repositório: " + repo.fullName);
        
        try {
            RepositoryAnalysis analysis = analyzeRepository(repo);
            if (analysis != null) {
                System.out.println("TESTE SUCESSO!");
                System.out.printf("Métricas CK: CBO=%.2f, DIT=%.2f, LCOM=%.2f\n", 
                    analysis.cboMean, analysis.ditMean, analysis.lcomMean);
                
                // Salvar resultado do teste
                Path testFile = dataPath.resolve("teste_1_repo.csv");
                saveResultsCSV(Arrays.asList(analysis), testFile);
                System.out.println("Arquivo de teste: " + testFile.toAbsolutePath());
            }
        } catch (Exception e) {
            System.err.println("ERRO no teste: " + e.getMessage());
        }
    }
    
    private RepositoryAnalysis analyzeRepository(RepositoryInfo repo) {
        try {
            // Clone do repositório
            Path repoLocalPath = cloneRepository(repo);
            if (repoLocalPath == null) {
                return null;
            }
            
            // Análise CK
            CKMetrics ckMetrics = runCKAnalysis(repoLocalPath);
            if (ckMetrics == null) {
                return null;
            }
            
            // Criar resultado
            RepositoryAnalysis analysis = new RepositoryAnalysis();
            analysis.fullName = repo.fullName;
            analysis.stars = repo.stars;
            analysis.ageInYears = repo.ageInYears;
            analysis.releasesCount = repo.releasesCount;
            analysis.size = repo.size;
            
            analysis.cboMean = ckMetrics.cboMean;
            analysis.cboMedian = ckMetrics.cboMedian;
            analysis.ditMean = ckMetrics.ditMean;
            analysis.ditMedian = ckMetrics.ditMedian;
            analysis.lcomMean = ckMetrics.lcomMean;
            analysis.lcomMedian = ckMetrics.lcomMedian;
            analysis.loc = ckMetrics.loc;
            analysis.classesCount = ckMetrics.classesCount;
            
            // Cleanup
            deleteDirectory(repoLocalPath);
            
            return analysis;
            
        } catch (Exception e) {
            System.out.println("Erro na análise do repositório " + repo.fullName + ": " + e.getMessage());
            return null;
        }
    }
    
    private Path cloneRepository(RepositoryInfo repo) {
        Path repoPath = reposPath.resolve(sanitizeFilename(repo.fullName));
        
        try {
            // Deletar se já existir
            if (Files.exists(repoPath)) {
                deleteDirectory(repoPath);
            }
            
            // Clone
            Git git = Git.cloneRepository()
                .setURI(repo.cloneUrl)
                .setDirectory(repoPath.toFile())
                .setDepth(1) // Clone shallow para ser mais rápido
                .call();
            
            git.close();
            return repoPath;
            
        } catch (GitAPIException e) {
            System.out.println("Erro no clone: " + e.getMessage());
            return null;
        } catch (Exception e) {
            System.out.println("Erro geral no clone: " + e.getMessage());
            return null;
        }
    }
    
    private CKMetrics runCKAnalysis(Path repoPath) {
        try {
            // Usar CK via comando externo (mais compatível)
            Path ckJar = Paths.get("ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar");
            Path outputDir = Paths.get("ck_output");
            Files.createDirectories(outputDir);
            
            // Executar CK
            ProcessBuilder pb = new ProcessBuilder(
                "java", "-jar", ckJar.toString(), 
                repoPath.toString(), "true", "0", "false", outputDir.toString()
            );
            
            Process process = pb.start();
            int exitCode = process.waitFor();
            
            if (exitCode != 0) {
                return null;
            }
            
            // Ler resultados do CSV gerado
            Path csvFile = outputDir.resolve("class.csv");
            if (!Files.exists(csvFile)) {
                return null;
            }
            
            return parseCKResults(csvFile);
            
        } catch (Exception e) {
            System.out.println("Erro na análise CK: " + e.getMessage());
            return null;
        }
    }
    
    private CKMetrics parseCKResults(Path csvFile) {
        try {
            List<String> lines = Files.readAllLines(csvFile);
            if (lines.size() <= 1) return null; // Apenas cabeçalho
            
            List<Double> cboValues = new ArrayList<>();
            List<Double> ditValues = new ArrayList<>();
            List<Double> lcomValues = new ArrayList<>();
            long totalLoc = 0;
            
            for (int i = 1; i < lines.size(); i++) {
                String[] parts = lines.get(i).split(",");
                if (parts.length >= 10) {
                    try {
                        cboValues.add(Double.parseDouble(parts[7])); // CBO column
                        ditValues.add(Double.parseDouble(parts[8])); // DIT column  
                        lcomValues.add(Double.parseDouble(parts[9])); // LCOM column
                        totalLoc += Long.parseLong(parts[3]); // LOC column
                    } catch (NumberFormatException e) {
                        // Skip invalid lines
                    }
                }
            }
            
            if (cboValues.isEmpty()) return null;
            
            CKMetrics metrics = new CKMetrics();
            metrics.cboMean = cboValues.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
            metrics.cboMedian = calculateMedian(cboValues);
            metrics.ditMean = ditValues.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
            metrics.ditMedian = calculateMedian(ditValues);
            metrics.lcomMean = lcomValues.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
            metrics.lcomMedian = calculateMedian(lcomValues);
            metrics.loc = totalLoc;
            metrics.classesCount = cboValues.size();
            
            return metrics;
            
        } catch (Exception e) {
            return null;
        }
    }
    
    private double calculateMedian(List<Double> values) {
        if (values.isEmpty()) return 0.0;
        
        Collections.sort(values);
        int size = values.size();
        
        if (size % 2 == 0) {
            return (values.get(size/2 - 1) + values.get(size/2)) / 2.0;
        } else {
            return values.get(size/2);
        }
    }
    
    private void saveRepositoriesCSV(List<RepositoryInfo> repositories, Path csvFile) throws IOException {
        try (CSVPrinter printer = new CSVPrinter(Files.newBufferedWriter(csvFile), CSVFormat.DEFAULT)) {
            // Cabeçalho
            printer.printRecord("full_name", "name", "owner", "description", "stars", "forks", 
                "size", "language", "created_at", "updated_at", "age_years", "releases_count", 
                "has_issues", "has_wiki", "default_branch", "clone_url");
            
            // Dados
            for (RepositoryInfo repo : repositories) {
                printer.printRecord(
                    repo.fullName, repo.name, repo.owner, repo.description,
                    repo.stars, repo.forks, repo.size, repo.language,
                    repo.createdAt,
                    repo.updatedAt,
                    repo.ageInYears, repo.releasesCount,
                    repo.hasIssues, repo.hasWiki, repo.defaultBranch, repo.cloneUrl
                );
            }
        }
    }
    
    private void saveResultsCSV(List<RepositoryAnalysis> results, Path csvFile) throws IOException {
        try (CSVPrinter printer = new CSVPrinter(Files.newBufferedWriter(csvFile), CSVFormat.DEFAULT)) {
            // Cabeçalho
            printer.printRecord("full_name", "stars", "age_years", "releases_count", "size",
                "cbo_mean", "cbo_median", "dit_mean", "dit_median", "lcom_mean", "lcom_median",
                "loc", "classes_count");
            
            // Dados
            for (RepositoryAnalysis analysis : results) {
                printer.printRecord(
                    analysis.fullName, analysis.stars, analysis.ageInYears, 
                    analysis.releasesCount, analysis.size,
                    String.format("%.2f", analysis.cboMean),
                    String.format("%.2f", analysis.cboMedian),
                    String.format("%.2f", analysis.ditMean),
                    String.format("%.2f", analysis.ditMedian),
                    String.format("%.2f", analysis.lcomMean),
                    String.format("%.2f", analysis.lcomMedian),
                    analysis.loc, analysis.classesCount
                );
            }
        }
    }
    
    private void printQuickStats(List<RepositoryAnalysis> results) {
        System.out.println("\n=== ESTATÍSTICAS RÁPIDAS ===");
        
        DoubleSummaryStatistics starsStats = results.stream().mapToDouble(r -> r.stars).summaryStatistics();
        DoubleSummaryStatistics cboStats = results.stream().mapToDouble(r -> r.cboMean).summaryStatistics();
        DoubleSummaryStatistics ditStats = results.stream().mapToDouble(r -> r.ditMean).summaryStatistics();
        DoubleSummaryStatistics lcomStats = results.stream().mapToDouble(r -> r.lcomMean).summaryStatistics();
        
        System.out.printf("Stars - Min: %.0f, Média: %.0f, Max: %.0f\n", 
            starsStats.getMin(), starsStats.getAverage(), starsStats.getMax());
        System.out.printf("CBO - Min: %.2f, Média: %.2f, Max: %.2f\n", 
            cboStats.getMin(), cboStats.getAverage(), cboStats.getMax());
        System.out.printf("DIT - Min: %.2f, Média: %.2f, Max: %.2f\n", 
            ditStats.getMin(), ditStats.getAverage(), ditStats.getMax());
        System.out.printf("LCOM - Min: %.2f, Média: %.2f, Max: %.2f\n", 
            lcomStats.getMin(), lcomStats.getAverage(), lcomStats.getMax());
    }
    
    private String sanitizeFilename(String name) {
        return name.replaceAll("[^a-zA-Z0-9._-]", "_");
    }
    
    private void deleteDirectory(Path path) {
        try {
            if (Files.exists(path)) {
                Files.walk(path)
                    .sorted(Comparator.reverseOrder())
                    .map(Path::toFile)
                    .forEach(File::delete);
            }
        } catch (IOException e) {
            System.out.println("Erro ao deletar diretório: " + e.getMessage());
        }
    }
    
    public static void main(String[] args) {
        try {
            Lab2JavaAnalyzer analyzer = new Lab2JavaAnalyzer();
            
            if (args.length > 0) {
                String command = args[0].toLowerCase();
                switch (command) {
                    case "s01":
                    case "lab02s01":
                        analyzer.executeLab02S01();
                        break;
                    case "s02":
                    case "lab02s02":
                        analyzer.executeLab02S02();
                        break;
                    default:
                        System.out.println("Comando inválido. Use: s01 ou s02");
                }
            } else {
                // Executar ambos
                analyzer.executeLab02S01();
                analyzer.executeLab02S02();
            }
            
        } catch (Exception e) {
            System.err.println("ERRO durante execução: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    // Classes auxiliares
    static class RepositoryInfo {
        public String fullName;
        public String name;
        public String owner;
        public String description;
        public int stars;
        public int forks;
        public int size;
        public String language;
        public String createdAt;
        public String updatedAt;
        public long ageInYears;
        public int releasesCount;
        public boolean hasIssues;
        public boolean hasWiki;
        public String defaultBranch;
        public String cloneUrl;
    }
    
    static class RepositoryAnalysis {
        public String fullName;
        public int stars;
        public long ageInYears;
        public int releasesCount;
        public int size;
        
        public double cboMean;
        public double cboMedian;
        public double ditMean;
        public double ditMedian;
        public double lcomMean;
        public double lcomMedian;
        
        public long loc;
        public int classesCount;
    }
    
    static class CKMetrics {
        public double cboMean;
        public double cboMedian;
        public double ditMean;
        public double ditMedian;
        public double lcomMean;
        public double lcomMedian;
        public long loc;
        public int classesCount;
    }
}
